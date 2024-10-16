import difflib
import fnmatch
import os
import subprocess
from datetime import datetime


class FileSystemComponent:

    def __init__(self, openai, working_directory='.'):
        self.openai = openai
        self.working_directory = working_directory
        self.gitignore_patterns = self.load_gitignore(self.working_directory)

    def open_file(self, file_path):
        # Implement file opening logic
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "File not found."

    def list_directory(self, dir_path):
        # Implement directory listing logic
        try:
            return os.listdir(dir_path)
        except FileNotFoundError:
            return "Directory not found."

    def change_directory(self, dir_name):
        # Update current path if changing directories
        new_path = os.path.join(self.working_directory, dir_name)
        if os.path.isdir(new_path):
            self.working_directory = new_path
            print(f"Changed directory to {self.working_directory}")
            return f"Changed directory to {self.working_directory}"
        else:
            print(f"Directory {new_path} not found.")
            return "Directory not found."

    def current_directory_tree(self, full=False):
        return self.get_directory_tree(self.working_directory, full)

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
                metadata = self.get_file_metadata(item_path)  # Get metadata
                directory_tree[item] = {
                    'content': self.process_file(item_path, full),
                    'metadata': metadata  # Include metadata in the return
                }
        return directory_tree

    def get_file_metadata(self, file_path):
        """Retrieve metadata for the specified file."""
        try:
            file_info = {
                'size': os.path.getsize(file_path),  # Size in bytes
                'git': self.get_git_history(file_path),
                'modified_time': os.path.getmtime(file_path),  # Last modified time
                'created_time': os.path.getctime(file_path),  # Creation time
                'extension': os.path.splitext(file_path)[1],  # File extension
                'is_hidden': file_path.startswith('.'),  # Check if the file is hidden
                'modified_time_iso': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),  # ISO format
                'created_time_iso': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),  # ISO format
            }
            return file_info
        except Exception as e:
            print(f"Error retrieving metadata for {file_path}: {e}")
            return {}

    def process_file(self, file_path, full=False):
        """Process each file: check extension, size, convert to text, and compress."""
        if full and os.path.isfile(file_path) and file_path.endswith((
                '.py', '.html', '.md', '.txt', '.css', '.gitignore',
                '.ts', '.tsx'
        )) and os.path.getsize(file_path) < 1 * 1024 * 1024:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    return content
            except UnicodeDecodeError as e:
                # print(f"UnicodeDecodeError: {str(e)} - Trying to read in binary mode.")
                try:
                    with open(file_path, 'rb') as file:
                        # Read bytes and decode with 'latin-1' or other fallback
                        content = file.read()
                        return content.decode('latin-1', errors='ignore')  # Ignore issues
                except Exception as e:
                    print(f"Could not read {file_path} in any encoding: {str(e)}")
            except Exception as e:
                print(f"Could not read {file_path}: {str(e)}")
        return None  # Or some placeholder that indicates processing failure

    def compress_content(self, content):
        return content

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

    def get_git_history(self, file_path):
        """Fetch a summary of git history for a specified file."""
        try:
            # Run the git log command and capture the output
            result = subprocess.run(
                ['git', 'log', '--oneline', file_path],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.working_directory
            )
            return result.stdout.strip()  # Stripping to remove any trailing spaces
        except subprocess.CalledProcessError as e:
            print(f"Error fetching git history: {e}")
            return "No git history found."