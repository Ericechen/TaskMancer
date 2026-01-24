import os
import re
from pathlib import Path
from typing import List, Dict, Any

class DirectoryScanner:
    def __init__(self, root_path: str, max_depth: int = 2):
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}

    def _extract_tags(self, project_path: Path, files: List[str]) -> List[str]:
        tags = []
        # 1. Tech Stack Detection
        if 'package.json' in files:
            tags.append('NodeJS')
            try:
                with open(project_path / 'package.json', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'vite' in content.lower(): tags.append('Vite')
                    if 'react' in content.lower(): tags.append('React')
                    if 'vue' in content.lower(): tags.append('Vue')
                    if 'next' in content.lower(): tags.append('NextJS')
            except: pass
            
        if 'requirements.txt' in files or 'pyproject.toml' in files:
            tags.append('Python')

        if 'docker-compose.yml' in files or 'Dockerfile' in files:
            tags.append('Docker')

        # 2. task.md Custom Tags (e.g. #personal #work)
        task_file = next((f for f in files if f.lower() == 'task.md'), None)
        if task_file:
            try:
                with open(project_path / task_file, 'r', encoding='utf-8') as f:
                    # Scan first 50 lines for hashtags
                    for _ in range(50):
                        line = f.readline()
                        if not line: break
                        found = re.findall(r'#(\w+)', line)
                        for tag in found:
                            if tag.lower() not in [t.lower() for t in tags]:
                                tags.append(tag)
            except: pass
            
        return tags

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scans for projects containing 'task.md'.
        Returns a list of dicts: {'name': project_name, 'path': absolute_path_to_project_root, 'tags': [...]}
        """
        projects = []
        
        for root, dirs, files in os.walk(self.root_path):
            current_path = Path(root)
            
            try:
                relative_path = current_path.relative_to(self.root_path)
                depth = len(relative_path.parts)
            except ValueError:
                depth = 0

            if depth > self.max_depth:
                dirs[:] = []
                continue

            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            task_files = [f for f in files if f.lower() == 'task.md']
            if task_files:
                projects.append({
                    'name': current_path.name if current_path != self.root_path else self.root_path.name,
                    'path': str(current_path),
                    'task_file': str(current_path / task_files[0]),
                    'tags': self._extract_tags(current_path, files)
                })
                
        return projects

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    
    scanner = DirectoryScanner(args.root)
    results = scanner.scan()
    print(f"Found {len(results)} projects:")
    for p in results:
        print(f" - {p['name']} {p.get('tags', [])}")
