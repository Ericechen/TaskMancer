from app.core.project_manager import ProjectManager

# Singleton instance
project_manager = ProjectManager()

def get_project_manager() -> ProjectManager:
    return project_manager
