import asyncio
import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.project_manager import ProjectManager

async def test():
    pm = ProjectManager()
    # Dummy setup to simulate lifecycle
    pm.load_projects()
    print("Projects loaded:", pm.watched_roots)
    try:
        state = await pm.get_current_state()
        print("State fetched successfully!")
        print("Project count:", len(state['projects']))
        print("System stats:", state['system'])
    except Exception as e:
        print("FAILED to fetch state!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
