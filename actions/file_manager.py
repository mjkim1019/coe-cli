import os

class FileManager:
    def __init__(self):
        self.session_files = set()

    def add(self, file_paths):
        messages = []
        for file_path in file_paths:
            self.session_files.add(file_path)
            if os.path.exists(file_path):
                messages.append(f"Added existing file: {file_path}")
            else:
                messages.append(f"Added new file (will be created on edit): {file_path}")
        return "\n".join(messages)
