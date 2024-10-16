import json
import os
import re
import threading
import weakref

import torch
from torch import cosine_similarity
from transformers import DistilBertTokenizer, DistilBertModel
from functools import lru_cache


class FileSystemAgent:
    def __init__(self, openai, chatbot, file_system):
        self.openai = openai
        self.chatbot_weakref = weakref.ref(chatbot)
        self.filename = None
        self.file_system = file_system
        self.lock = threading.Lock()
        self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
        self.model = DistilBertModel.from_pretrained("distilbert-base-uncased").half()  # Use half-precision
        self.open_file_phrases = ["open file", "read from file", "access document", "open directory", "open folder"]
        self.intent_phrases = {
            "file": "file",
            "folder": "folder directory",
        }
        self.intent_vectors = self._vectorize_intents(self.intent_phrases)
        self.open_file_vectors = self._vectorize_phrases(self.open_file_phrases)

    def change_directory(self, dir_name):
        with self.lock:  # Lock to prevent race conditions
            new_path = os.path.join(self.file_system.working_directory, dir_name)
            if os.path.isdir(new_path):
                self.working_directory = new_path
                print(f"Changed directory to {self.working_directory}")
                return f"Changed directory to {self.working_directory}"
            else:
                print(f"Directory {new_path} not found.")
                return "Directory not found."

    def fill_in_command(self, user_id, request, openai, chat_history):
        """Generate responses using OpenAI API while adhering to ethical principles."""
        messages = chat_history[-5:0]
        messages.append({
            "role": "system",
            "content": self.file_system.execute_command('dir'),
        })

        messages.append({
            "role": "system",
            "content": "The user wants to run the next command. Please fill in any variables as you would best generate them and output either a single line or a ```bash",
        })
        messages.append({
            "role": "system",
            "content": request,
        })

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Using the more efficient model
                messages=messages,
                max_tokens=1000,
            ).choices[0].message.content.strip()

            return response
        except Exception as e:
            print(e)
            return e

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

        output = {
            "directory" : {
                "path" : self.file_system.working_directory,
                "content": self.file_system.current_directory_tree(True)
            }
        }
        return output

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
        #
        # user_vector = self._vectorize_input(user_prompt)
        # similarities = {
        #     intent: self.cosine_similarity(user_vector, vector)
        #     for intent, vector in self.intent_vectors.items()
        # }
        #
        # best_intent = max(similarities, key=similarities.get)
        if input(f"Do you want to open a directory (y/n)?") != 'y':
            return False

        prompt = self._select_folder(user_prompt)
        root.destroy()

        return prompt

    def cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between two vectors."""
        a_norm = vec_a / vec_a.norm(p=2)
        b_norm = vec_b / vec_b.norm(p=2)
        return (a_norm @ b_norm.T).item()  # Return the similarity score as a float

    def _select_folder(self, user_prompt):
            from tkinter.filedialog import askdirectory
            dir_name = askdirectory()
            if dir_name is not None:
                self.file_system.change_directory(dir_name)


    def extract_commands(self, request):
        """Extract commands and associated data from a request."""
        pattern = r'```(\w+)\n(.*?)```'  # Matches commands within triple backticks
        matches = re.findall(pattern, request, re.DOTALL)
        commands = [{ 'cmd_type': cmd_type, 'data': data.strip() } for cmd_type, data in matches]
        return commands

    def handle_commands(self, user_id, request, chat_history):
        if request.startswith('~~'):
            command_results = []
            if request.startswith('~~~'):

                request_command = request[3:].strip()  # Strip '~~~'
                updated_command = self.fill_in_command(user_id, request_command, self.openai, chat_history)

                if '```' in updated_command:  # Check for code snippets
                    # Extract bash/PowerShell commands from the request
                    commands = self.extract_commands(updated_command)
                    for command in commands:

                        if input(f"Do you want to run the command? (y/n) {updated_command}") == 'y':
                            command_result = self.file_system.execute_command(command["data"])
                            command_results.append([command, command_result])
                        else:
                            break

            else:
                command =  request[2:].strip()  # Strip '~~'
                if input(f"Do you want to run the command? (y/n) {command}") == 'y':
                    print(command)
                    command_results =[[command, self.file_system.execute_command(command)]]

            return command_results

        return None