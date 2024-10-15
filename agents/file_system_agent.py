import difflib
import json
import os
import fnmatch
import torch
from torch import cosine_similarity
from transformers import DistilBertTokenizer, DistilBertModel
from functools import lru_cache


class FileSystemAgent:
    def __init__(self):
        self.filename = None
        self.foldername = None
        self.initial_file_value = ""
        self.initial_folder_value = ""
        self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = DistilBertModel.from_pretrained("distilbert-base-uncased").half()  # Use half-precision
        self.open_file_phrases = ["open file", "read from file", "access document", "open directory", "open folder"]
        self.intent_phrases = {
            "file": "file",
            "folder": "folder directory",
        }
        self.intent_vectors = self._vectorize_intents(self.intent_phrases)
        self.open_file_vectors = self._vectorize_phrases(self.open_file_phrases)
        self.full_tree = {}
        self.gitignore_patterns = self.load_gitignore()  # Load .gitignore patterns

    def _vectorize_phrases(self, phrases):
        # Batch tokenization and processing for efficiency
        inputs = self.tokenizer(phrases, return_tensors='pt', padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Return a list of tensors (one per phrase) rather than a single tensor
        return [outputs.last_hidden_state[i].mean(dim=0) for i in range(len(phrases))]

    def _vectorize_intents(self, phrases):
        vectors = {}
        for key, phrase in phrases.items():
            inputs = self.tokenizer(phrase, return_tensors='pt')
            with torch.no_grad():
                outputs = self.model(**inputs)
                vectors[key] = outputs.last_hidden_state.mean(dim=1)
        return vectors

    @lru_cache(maxsize=128)  # Cache frequently used inputs for faster access
    def _vectorize_input(self, user_input):
        inputs = self.tokenizer(user_input, return_tensors='pt')
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

    def handle_request(self, request):
        """Handle incoming requests to read or write files."""
        if self.check_open_file(request):
            user_input = self.ask_open(request)
        return self.get_system_message()

    def check_open_file(self, user_prompt):
        """Determine if the user prompt indicates intent to open a file."""
        user_vector = self._vectorize_input(user_prompt)

        # Ensure open_file_vectors is a list of tensors and stack them
        open_file_vector_tensor = torch.stack(self.open_file_vectors)

        # Compute cosine similarity
        similarities = cosine_similarity(user_vector, open_file_vector_tensor)

        # Check if maximum similarity is above threshold
        if torch.max(similarities) > 0.9:  # Adjust threshold as necessary
            return True
        return False

    def get_prompt_data(self):
        file_content = self._current_file()
        directory_content = self._current_folder()

        output = {
            "file" : {
                "path": self.filename or "No file",
                "content": file_content or "No content"
            },
            "directory" : {
                "path" : self.foldername or "No directory",
                "content": directory_content or "No content"
            }
        }

        if (file_content and self.initial_file_value
                and len(file_content) != len(self.initial_file_value)):
            output["file"]["original_content"] = self.compute_diffs(self.initial_file_value, file_content)

        if (directory_content and self.initial_folder_value
                and len(directory_content) != len(self.initial_folder_value)):
            output["file"]["original_content"] = self.compute_diffs(self.initial_folder_value, directory_content)

        return output

    def compute_diffs(self, init_state, current_state):
        """Compute the differences between initial and current directory states."""

        # Create a diff
        diff = list(difflib.unified_diff(
            init_state.splitlines(keepends=True),
            current_state.splitlines(keepends=True),
            fromfile='initial_state.json',
            tofile='current_state.json',
            lineterm=''
        ))

        return ''.join(diff)

    def get_prompt(self):
        out = "There are currently no files or folders in context"
        data = self.get_prompt_data()
        out = f"The user is currently working with these files and folders. {json.dumps(self.get_prompt_data())}"
        return out

    def get_system_message(self):
        return {
            "role": "user",
            "content": self.get_prompt(),
        }

    def ask_open(self, user_prompt):
        """Prompt user to select a file if specified in the user prompt."""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the Tkinter root window

        root.attributes('-topmost', True)
        root.update()

        user_vector = self._vectorize_input(user_prompt)
        similarities = {
            intent: self.cosine_similarity(user_vector, vector)
            for intent, vector in self.intent_vectors.items()
        }

        best_intent = max(similarities, key=similarities.get)
        if input(f"Do you want to open a {best_intent} (y/n)?") != 'y':
            return False
        prompt = self._select_folder(user_prompt) if best_intent == 'folder' else self._select_file(user_prompt)
        root.destroy()

        return prompt

    def cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between two vectors."""
        a_norm = vec_a / vec_a.norm(p=2)
        b_norm = vec_b / vec_b.norm(p=2)
        return (a_norm @ b_norm.T).item()  # Return the similarity score as a float

    def _select_file(self, user_prompt):
        from tkinter.filedialog import askopenfilename
        filename = askopenfilename()  # Open the file dialog
        self.filename = filename
        self.initial_file_value = self._current_file()

    def _current_file(self):
        filename = self.filename
        if filename is None:
            return None
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                file_content = file.read()
                return file_content

        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return f"Error reading {filename}"

    def _select_folder(self, user_prompt):
            from tkinter.filedialog import askdirectory
            foldername = askdirectory()
            self.foldername = foldername
            self.initial_folder_value = self._current_folder()

    def _current_folder(self):
        try:
            foldername = self.foldername
            if foldername is None:
                return None
            dir_content = self.get_directory_tree(foldername, full=True)
            return dir_content
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return f"Error reading: {self.foldername}"

    def load_gitignore(self, path="."):
        """Load patterns from .gitignore file."""
        gitignore_path = os.path.join(path, '.gitignore')
        patterns = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return patterns

    def is_hidden(self, filename):
        """Check if a file is hidden (starts with a dot)."""
        return filename.startswith('.')

    def is_ignored(self, filename):
        """Check if a file is ignored by .gitignore."""
        return any(fnmatch.fnmatch(filename, pattern) for pattern in self.gitignore_patterns)

    def get_directory_tree(self, path=".", full=False):
        """Recursively get the directory tree starting from the given path."""
        directory_tree = {}
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if self.is_hidden(item) or self.is_ignored(item):
                continue
            if os.path.isdir(item_path):
                directory_tree[item] = self.get_directory_tree(item_path, full)
            else:
                directory_tree[item] = self.process_file(item_path, full)
        return directory_tree

    def process_file(self, file_path, full=False):
        """Process each file: check extension, size, convert to text, and compress."""
        if full and os.path.isfile(file_path) and file_path.endswith((
                '.py','.html','.md', '.txt', '.css', '.gitignore',
                '.ts',
                '.tsx'
        )) and os.path.getsize(file_path) < 1 * 1024 * 1024:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    compressed_content = self.compress_content(content)
                    self.full_tree[file_path] = compressed_content
                    return compressed_content
            except (UnicodeDecodeError, IOError) as e:
                print(f"Could not read {file_path}: {str(e)}")

    def compress_content(self, content):
        return content

    # def handle_request(self, request):
    #     """Handle incoming requests to read or write files."""
    #     request_analysis = self.analyze_request(request)
    #     action = request_analysis.get("action")
    #
    #     if action == "read":
    #         file_to_read = request_analysis.get("file")
    #         if not file_to_read:
    #             return "Error: No file specified for reading."
    #         return self.read_file(file_to_read)
    #
    #     elif action == "write":
    #         file_to_write = request_analysis.get("file")
    #         content_to_write = request_analysis.get("content")
    #         if not file_to_write or content_to_write is None:
    #             return "Error: Insufficient arguments for writing."
    #         return self.write_file(file_to_write, content_to_write)
    #
    #     return "Error: Unrecognized command."

    def read_file(self, filename):
        """Read a file and return its contents."""
        try:
            with open(filename, 'r') as file:
                content = file.read()
            return f"Contents of {filename}:\n{content}"
        except FileNotFoundError:
            return f"Error: {filename} not found."
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, filename, content):
        """Write content to a file."""
        try:
            with open(filename, 'w') as file:
                file.write(content)
            return f"Successfully wrote to {filename}."
        except Exception as e:
            return f"Error writing to file: {str(e)}"

    # def analyze_request(self, request):
    #     """Analyze the user's request and return structured intent data."""
    #     request = request.lower().strip()
    #
    #     if request.startswith("read "):
    #         file_name = request[len("read "):].strip()
    #         return {"action": "read", "file": file_name}
    #     elif request.startswith("write "):
    #         parts = request[len("write "):].strip().split(" ", 1)
    #         if len(parts) < 2:
    #             return {"action": "write", "file": None, "content": None}
    #         file_name = parts[0]
    #         content = parts[1]
    #         return {"action": "write", "file": file_name, "content": content}
    #     elif request.startswith("delete "):
    #         file_name = request[len("delete "):].strip()
    #         return {"action": "delete", "file": file_name}
    #     elif request.startswith("list"):
    #         return {"action": "list", "file": None}
    #
    #     return {"action": "unknown"}
