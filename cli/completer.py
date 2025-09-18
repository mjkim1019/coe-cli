import glob
import os
from prompt_toolkit.completion import Completer, Completion

class PathCompleter(Completer):
    def __init__(self):
        self._file_cache = {}
        
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Trigger completion only when '@' is present
        at_pos = text.rfind('@')
        if at_pos == -1:
            return

        # The word to complete starts after the '@'
        word_to_complete = text[at_pos:]
        search_term = word_to_complete[1:]
        
        # Show completions immediately when '@' is typed (no minimum length required)
        # This allows users to see all available files when they type '@'

        # Get cached or fresh file list
        project_paths = self._get_project_files()

        # Filter paths based on the search term with smart matching
        matches = []
        
        for path in project_paths:
            # Skip if file doesn't exist anymore
            if not os.path.exists(path):
                continue
                
            path_lower = path.lower()
            search_lower = search_term.lower()
            
            # Different matching strategies
            match_score = 0
            match_reason = ""
            
            # Get relative path and filename for better matching
            filename = os.path.basename(path)
            filename_lower = filename.lower()
            
            # If no search term (just '@'), show all files with priority-based scoring
            if len(search_term) == 0:
                # Give higher priority to common project files
                if filename in ['main.py', 'app.py', 'index.js', 'main.c', 'README.md']:
                    match_score = 70
                    match_reason = "Important file"
                elif path.startswith(('cli/', 'src/', 'actions/', 'lib/')):
                    match_score = 60
                    match_reason = "Project file"
                else:
                    match_score = 50
                    match_reason = "All files"
            # 1. Exact filename match (highest priority)
            elif search_lower == filename_lower:
                match_score = 100
                match_reason = "Exact filename"
            # 2. Filename starts with search term
            elif filename_lower.startswith(search_lower):
                match_score = 90
                match_reason = "Filename starts"
            # 3. Partial path match (e.g., "cli/ma" matches "cli/main.py")
            elif search_lower in path_lower and '/' in search_term:
                if path_lower.startswith(search_lower):
                    match_score = 85
                    match_reason = "Path starts"
                else:
                    match_score = 75
                    match_reason = "Path contains"
            # 4. Filename contains search term
            elif search_lower in filename_lower:
                match_score = 80
                match_reason = "Filename contains"
            # 5. Path ends with search term (relative path matching)
            elif path_lower.endswith(search_lower):
                match_score = 70
                match_reason = "Path ends with"
            # 6. Any part of path contains search term
            elif search_lower in path_lower:
                match_score = 60
                match_reason = "Path contains"
            # 7. No match
            else:
                continue
            
            # Determine if it's a file or directory
            if os.path.isfile(path):
                file_type = "File"
                # Boost score for project-relevant file types
                if path.endswith(('.py', '.c', '.h', '.sql', '.xml', '.js', '.md')):
                    match_score += 5
                # Extra boost for Python files in a Python project
                if path.endswith('.py'):
                    match_score += 3
            elif os.path.isdir(path):
                file_type = "Directory"
                # Slight boost for common project directories
                if filename in ['src', 'lib', 'tests', 'actions', 'cli', 'core']:
                    match_score += 2
            else:
                continue  # Skip if neither file nor directory
            
            matches.append({
                'path': path,
                'score': match_score,
                'type': file_type,
                'reason': match_reason
            })
        
        # Sort by score (highest first), then by path length (shorter first)
        matches.sort(key=lambda x: (-x['score'], len(x['path'])))
        
        # Yield completions
        for match in matches[:15]:  # Limit to top 15 matches for better UX
            display_meta = f"{match['type']} - {match['reason']}"
            
            yield Completion(
                f"@{match['path']}",                # Text to be inserted (keep @ symbol)
                start_position=-len(word_to_complete), # Replace from the '@'
                display=match['path'],              # How it appears in the completion menu
                display_meta=display_meta          # A little note next to the suggestion
            )
    
    def _get_project_files(self):
        """Get project files with caching and improved filtering"""
        cache_key = 'project_files'
        
        # Simple cache check (in production, you'd want timestamp-based invalidation)
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]
        
        project_paths = set()
        
        try:
            # 1. Get all files recursively
            all_paths = glob.glob('**/*', recursive=True)
            
            # 2. Filter out unwanted paths
            exclude_patterns = [
                '.git/', '__pycache__/', 'node_modules/', '.venv/', 'venv/',
                '.pytest_cache/', '.mypy_cache/', '*.pyc', '*.pyo',
                '.DS_Store', '*.egg-info/', 'dist/', 'build/'
            ]
            
            for path in all_paths:
                # Skip if matches any exclude pattern
                if any(pattern.rstrip('/') in path or path.endswith(pattern.lstrip('*')) 
                      for pattern in exclude_patterns):
                    continue
                
                # Only include files and directories that exist
                if os.path.exists(path):
                    project_paths.add(path)
            
            # 3. Add current directory files explicitly
            try:
                current_dir_files = [f for f in os.listdir('.') 
                                   if os.path.isfile(f) and not f.startswith('.')]
                project_paths.update(current_dir_files)
            except (OSError, PermissionError):
                pass
            
        except Exception:
            # Fallback to basic file listing
            try:
                project_paths = set(glob.glob('*'))
            except Exception:
                project_paths = set()
        
        # Convert to sorted list for consistent ordering
        result = sorted(list(project_paths))
        
        # Cache the result
        self._file_cache[cache_key] = result
        
        return result
