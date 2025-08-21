import glob
import os
from prompt_toolkit.completion import Completer, Completion

class PathCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Trigger completion only when '@' is present
        at_pos = text.rfind('@')
        if at_pos == -1:
            return

        # The word to complete starts after the '@'
        word_to_complete = text[at_pos:]
        search_term = word_to_complete[1:]

        # Find all files and directories recursively, excluding common noise
        try:
            all_paths = glob.glob('**/*', recursive=True)
            project_paths = [
                f for f in all_paths
                if '.git' not in f and '__pycache__' not in f and 'node_modules' not in f
            ]
        except Exception:
            project_paths = [] # Handle potential errors during glob

        # Filter paths based on the search term
        for path in project_paths:
            if search_term.lower() in path.lower():
                # Determine if it's a file or directory
                if os.path.isfile(path):
                    meta = "File"
                elif os.path.isdir(path):
                    meta = "Directory"
                else:
                    continue  # Skip if neither file nor directory
                
                yield Completion(
                    path,                      # Text to be inserted
                    start_position=-len(word_to_complete), # Replace from the '@'
                    display=path,              # How it appears in the completion menu
                    display_meta=meta         # A little note next to the suggestion
                )
