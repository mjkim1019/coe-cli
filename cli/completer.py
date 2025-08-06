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

        # Find all files recursively, excluding common noise
        try:
            all_files = glob.glob('**/*', recursive=True)
            project_files = [
                f for f in all_files
                if os.path.isfile(f) and '.git' not in f and '__pycache__' not in f
            ]
        except Exception:
            project_files = [] # Handle potential errors during glob

        # Filter files based on the search term
        for path in project_files:
            if search_term.lower() in path.lower():
                yield Completion(
                    path,                      # Text to be inserted
                    start_position=-len(word_to_complete), # Replace from the '@'
                    display=path,              # How it appears in the completion menu
                    display_meta="File"      # A little note next to the suggestion
                )
