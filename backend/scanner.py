import os
from pathlib import Path
from typing import List, Dict

class DirectoryScanner:
    def __init__(self, root_path: str, max_depth: int = 2):
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}

    def scan(self) -> List[Dict[str, str]]:
        """
        Scans for projects containing 'task.md'.
        Returns a list of dicts: {'name': project_name, 'path': absolute_path_to_project_root}
        """
        projects = []
        
        # Walk through the directory top-down
        for root, dirs, files in os.walk(self.root_path):
            current_path = Path(root)
            
            # reliable depth calculation
            try:
                relative_path = current_path.relative_to(self.root_path)
                depth = len(relative_path.parts)
            except ValueError:
                depth = 0 # should not happen if we walk from root

            # Check depth limit
            if depth > self.max_depth:
                # Modifying dirs in-place to stop walking deeper
                dirs[:] = []
                continue

            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            if 'task.md' in files:
                projects.append({
                    'name': current_path.name if current_path != self.root_path else self.root_path.name,
                    'path': str(current_path),
                    'task_file': str(current_path / 'task.md')
                })
                
        return projects

if __name__ == "__main__":
    # Test execution
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    
    scanner = DirectoryScanner(args.root)
    results = scanner.scan()
    print(f"Found {len(results)} projects:")
    for p in results:
        print(f" - {p['name']}: {p['task_file']}")
