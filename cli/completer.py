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

        # Find all files and directories, including relative path completion
        project_paths = []
        
        try:
            # 1. Standard recursive search
            all_paths = glob.glob('**/*', recursive=True)
            standard_paths = [
                f for f in all_paths
                if '.git' not in f and '__pycache__' not in f and 'node_modules' not in f
            ]
            project_paths.extend(standard_paths)
            
            # 2. If search term contains path separators, try directory-specific search
            if '/' in search_term:
                dir_part = os.path.dirname(search_term)
                if os.path.isdir(dir_part):
                    # Search within the specific directory
                    dir_specific = glob.glob(f"{dir_part}/**/*", recursive=True)
                    project_paths.extend([f for f in dir_specific if f not in project_paths])
            
            # 3. Common project directories (higher priority)
            common_dirs = ['tests', 'src', 'lib', 'actions', 'cli']
            for common_dir in common_dirs:
                if os.path.isdir(common_dir):
                    common_paths = glob.glob(f"{common_dir}/**/*", recursive=True)
                    project_paths.extend([f for f in common_paths if f not in project_paths])
            
        except Exception:
            project_paths = [] # Handle potential errors during glob

        # Filter paths based on the search term with smart matching
        matches = []
        
        for path in project_paths:
            path_lower = path.lower()
            search_lower = search_term.lower()
            
            # Different matching strategies
            match_score = 0
            match_reason = ""
            
            # 1. Exact filename match (highest priority)
            filename = os.path.basename(path)
            if search_lower == filename.lower():
                match_score = 100
                match_reason = "Exact filename"
            # 2. Filename starts with search term
            elif filename.lower().startswith(search_lower):
                match_score = 90
                match_reason = "Filename starts"
            # 3. Filename contains search term
            elif search_lower in filename.lower():
                match_score = 80
                match_reason = "Filename contains"
            # 4. Path ends with search term (relative path matching)
            elif path_lower.endswith(search_lower):
                match_score = 70
                match_reason = "Path ends with"
            # 5. Any part of path contains search term
            elif search_lower in path_lower:
                match_score = 60
                match_reason = "Path contains"
            # 6. No match
            else:
                continue
            
            # Determine if it's a file or directory
            if os.path.isfile(path):
                file_type = "File"
                # Boost score for certain file types
                if path.endswith(('.c', '.h', '.sql', '.xml')):
                    match_score += 5
            elif os.path.isdir(path):
                file_type = "Directory"
            else:
                continue  # Skip if neither file nor directory
            
            matches.append({
                'path': path,
                'score': match_score,
                'type': file_type,
                'reason': match_reason
            })
        
        # Sort by score (highest first) and limit results
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Yield completions
        for match in matches[:20]:  # Limit to top 20 matches
            display_meta = f"{match['type']} ({match['reason']})"
            
            yield Completion(
                match['path'],                    # Text to be inserted
                start_position=-len(word_to_complete), # Replace from the '@'
                display=match['path'],            # How it appears in the completion menu
                display_meta=display_meta        # A little note next to the suggestion
            )
