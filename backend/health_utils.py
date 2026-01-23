import os
from pathlib import Path
from typing import Dict, Any, List

class HealthChecker:
    def __init__(self, project_path: str):
        self.path = Path(project_path)
        self.ignored_dirs = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', '.next', '.nuxt'}

    def get_health_status(self) -> Dict[str, Any]:
        """Checks for common environment markers."""
        health = {
            "has_node_modules": (self.path / "node_modules").exists(),
            "has_venv": (self.path / ".venv").exists() or (self.path / "venv").exists(),
            "is_npm": (self.path / "package.json").exists(),
            "is_python": (self.path / "requirements.txt").exists() or (self.path / "pyproject.toml").exists() or (self.path / "setup.py").exists(),
        }
        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates basic codebase metrics."""
        total_loc = 0
        lang_dist = {}
        total_files = 0
        total_size = 0

        # Extensions to track
        track_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.vue': 'Vue',
            '.html': 'HTML',
            '.css': 'CSS',
            '.md': 'Markdown',
            '.json': 'JSON'
        }

        try:
            for root, dirs, files in os.walk(self.path):
                # Prune ignored directories
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                for file in files:
                    file_path = Path(root) / file
                    ext = file_path.suffix.lower()
                    
                    if ext in track_extensions:
                        lang = track_extensions[ext]
                        lang_dist[lang] = lang_dist.get(lang, 0) + 1
                        
                        # LOC calculation removed for performance
                        pass
                    
                    total_files += 1
                    try:
                        total_size += file_path.stat().st_size
                    except:
                        pass

            return {
                "loc": total_loc,
                "languages": lang_dist,
                "fileCount": total_files,
                "size": total_size
            }
        except Exception as e:
            return {"error": str(e)}

def get_project_health_report(path: str) -> Dict[str, Any]:
    checker = HealthChecker(path)
    return {
        "health": checker.get_health_status(),
        "metrics": checker.get_metrics()
    }
