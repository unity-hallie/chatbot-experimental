import difflib
import fnmatch
import json
import os
import subprocess
import weakref
from datetime import datetime


class FileSystemComponent:
    def __init__(self, openai, config_path='./config/fsc_config.json'):
        self.openai = openai
        self.metadata_cache = {}
        self.content_cache = {}
        self.config_path = config_path
        self.settings = self.load_json(config_path) or {
            'cwd' : './sandbox'
        }
        self.working_directory = self.settings.get('cwd', './sandbox')
        self.gitignore_patterns = self.load_gitignore(self.working_directory)



    def save_settings(self):
        self.write_file(self.config_path, json.dumps(self.settings, indent=2))

    def load_json(self, path):
        """Load previously saved variables from a file, if available."""
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None  # Return None if no saved file exists
        except json.JSONDecodeError:
            print("Error: Could not parse saved variables.")
            return None

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
            self.settings["cwd"] = new_path
            self.save_settings()
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
                    'content': self.process_file(item_path, metadata, full),
                    'metadata': metadata  # Include metadata in the return
                }
        return directory_tree

    def get_file_metadata(self, file_path):
        """Retrieve metadata for the specified file."""
        try:
            cached = self.metadata_cache.get(file_path)
            modified_time =os.path.getmtime(file_path)

            if cached and modified_time <= cached["modified_time"]:
                cached["from_cache"] = True
                return cached

            file_info = {
                'size': os.path.getsize(file_path),  # Size in bytes
                'git': self.get_git_history(file_path),
                'modified_time': modified_time,  # Last modified time
                'created_time': os.path.getctime(file_path),  # Creation time
                'extension': os.path.splitext(file_path)[1],  # File extension
                'is_hidden': file_path.startswith('.'),  # Check if the file is hidden
                'modified_time_iso': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),  # ISO format
                'created_time_iso': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),  # ISO format
                'from_cache': False,
            }
            self.metadata_cache[file_path] = file_info
            return file_info
        except Exception as e:
            print(f"Error retrieving metadata for {file_path}: {e}")
            return {}

    def process_file(self, file_path, metadata, full=False):
        """Process each file: check extension, size, convert to text, and compress."""
        if metadata['from_cache'] and file_path in self.content_cache:
            return self.content_cache[file_path]

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
        print("getting git history for", file_path)
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

    def execute_command(self, command):
        """Executes a given command in the Windows shell and returns the output."""
        path = self.working_directory
        try:
            # Use subprocess to execute the command
            print(f"Executing command: {command} in {path}")  # Debug output
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=path)

            # Return stdout or handle errors
            if result.returncode == 0:
                return result.stdout.strip()  # Return the command output
            else:
                return f"Error: {result.stderr.strip()}"  # Return error message if any
        except Exception as e:
            return f"An error occurred while executing the command: {str(e)}"
