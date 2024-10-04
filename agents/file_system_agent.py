import os
import fnmatch

from states.world_state import WorldState


class FileSystemAgent:
    def __init__(self):
        self.full_tree = {}
        self.gitignore_patterns = self.load_gitignore()  # Load .gitignore patterns

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
                continue  # Skip hidden and ignored files
            if os.path.isdir(item_path):
                directory_tree[item] = self.get_directory_tree(item_path, full)  # Recurse into subdirectory
            else:
                directory_tree[item] = self.process_file(item_path, full)  # It's a file
        return directory_tree

    def process_file(self, file_path, full=False):
        """Process each file: check extension, size, convert to text, and compress."""
        # Check if the file is a .py or .html file and smaller than 1 MB
        if full and os.path.isfile(file_path) and file_path.endswith(('.py', '.html')) and os.path.getsize(file_path) < 1 * 1024 * 1024:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    compressed_content = self.compress_content(content)
                    self.full_tree[file_path] = compressed_content  # Store the compressed content
                    return compressed_content
            except (UnicodeDecodeError, IOError) as e:
                print(f"Could not read {file_path}: {str(e)}")


    def compress_content(self, content):
        return content

    def handle_request(self, request):
        """Handle incoming requests to read or write files."""
        command, *args = request.split()  # Basic command parsing (space-separated)

        if command == "read":
            if args:
                return self.read_file(args[0])  # Pass the filename
            else:
                return "Error: No file specified for reading."

        elif command == "write":
            if len(args) >= 2:
                filename = args[0]
                content = " ".join(args[1:])  # Join the rest as content
                return self.write_file(filename, content)
            else:
                return "Error: Insufficient arguments for writing."

        return "Error: Unrecognized command."

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

    def reload(self):
        """Reload the directory tree if needed."""
        self.directory_tree = self.get_directory_tree(True)  # Reset and refresh the directory tree
        print("FileSystemAgent reloaded.")

    def get_src(self):
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"


    def handle_request(self, request):
        """ Handle file read/write requests based on the provided request. """

        request_analysis = self.analyze_request(request)  # Analyze user request to determine action
        action = request_analysis.get("action")

        if action == "read":
            file_to_read = request_analysis.get("file")
            if not file_to_read:
                return "Error: No file specified for reading."
            return self.read_file(file_to_read)

        elif action == "write":
            file_to_write = request_analysis.get("file")
            content_to_write = request_analysis.get("content")
            if not file_to_write or content_to_write is None:
                return "Error: Insufficient arguments for writing."

            return self.write_file(file_to_write, content_to_write)

        else:
            return "Error: Unrecognized command."


    def read_file(self, filename):
        """ Read a file and return its contents. """
        try:
            with open(filename, 'r') as file:
                content = file.read()
            return f"Contents of {filename}:\n{content}"
        except FileNotFoundError:
            return f"Error: {filename} not found."
        except Exception as e:
            return f"Error reading file: {str(e)}"


    def write_file(self, filename, content):
        """ Write content to a file. """
        try:
            with open(filename, 'w') as file:
                file.write(content)
            return f"Successfully wrote to {filename}."
        except Exception as e:
            return f"Error writing to file: {str(e)}"

    def analyze_request(self, request):
        """ Analyze the user's request and return structured intent data. """

        # Lowercase the request for easier matching
        request = request.lower().strip()

        if request.startswith("read "):
            # Extract the filename to read
            file_name = request[len("read "):].strip()
            return {
                "action": "read",
                "file": file_name
            }
        elif request.startswith("write "):
            # Extract the filename and content to write
            parts = request[len("write "):].strip().split(" ", 1)
            if len(parts) < 2:
                return {"action": "write", "file": None, "content": None}  # Insufficient arguments

            file_name = parts[0]  # First part is the filename
            content = parts[1]  # Everything else is the content
            return {
                "action": "write",
                "file": file_name,
                "content": content
            }

        elif request.startswith("delete "):
            # Extract the filename to delete
            file_name = request[len("delete "):].strip()
            return {
                "action": "delete",
                "file": file_name
            }

        elif request.startswith("list"):
            # Return the action for listing files in a directory
            return {
                "action": "list",
                "file": None  # No specific file needed for listing
            }

        # Add more command types as needed...

        return {"action": "unknown"}  # For unrecognized commands


    def get_special_instructions(self):
        return "This agent handles file-related operations. Ensure to format responses with technical precision."