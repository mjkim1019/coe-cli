import os

class FileManager:
    def __init__(self):
        self.files = {}

    def add(self, file_paths):
        messages = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.files[file_path] = content
                    line_count = len(content.splitlines())
                    char_count = len(content)
                    messages.append(f"Read {file_path} ({line_count} lines, {char_count} chars)")
                except Exception as e:
                    messages.append(f"Error reading file {file_path}: {e}")
            else:
                self.files[file_path] = ""  # Store empty content for new files
                messages.append(f"Added new file (will be created on edit): {file_path}")
        return "\n".join(messages)
