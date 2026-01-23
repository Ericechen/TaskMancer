import asyncio
import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from scanner import DirectoryScanner
from watcher_service import DebouncedEventHandler
from task_parser import TaskParser

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TaskMancer.Main")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class RootPathRequest(BaseModel):
    path: str

# --- Global State ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

import json

class ProjectManager:
    def __init__(self):
        self.watched_roots: Set[str] = set()
        self.connection_manager = ConnectionManager()
        self.observer = Observer()
        self.event_handler = None
        self.config_file = "projects.json"
        self.discovery_root = ""
        self.watches = {} # Map path -> ObservedWatch

    def start_watcher(self):
        self.event_handler = DebouncedEventHandler(
            loop=asyncio.get_running_loop(),
            callback=self.notify_clients,
            debounce_seconds=0.5
        )
        self.observer.start()
        self.load_projects()

    def stop_watcher(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def load_projects(self):
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paths = data.get('roots', [])
                self.discovery_root = data.get('discovery_root', "")
                logger.info(f"Loading {len(paths)} projects from config. Discovery Root: {self.discovery_root}")
                for path in paths:
                    try:
                        self.add_root(path, save=False)
                    except Exception as e:
                        logger.error(f"Failed to load project {path}: {e}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def save_projects(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "roots": list(self.watched_roots),
                    "discovery_root": self.discovery_root
                }, f, indent=2)
            logger.info("Projects configuration saved.")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def add_root(self, path: str, save: bool = True):
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        if abs_path in self.watched_roots:
            return # Already watched

        logger.info(f"Adding root: {abs_path}")
        self.watched_roots.add(abs_path)
        
        if self.event_handler:
            watch = self.observer.schedule(self.event_handler, abs_path, recursive=True)
            self.watches[abs_path] = watch
        
        if save:
            self.save_projects()
            asyncio.create_task(self.notify_clients())

    def remove_root(self, path: str):
        abs_path = os.path.abspath(path)
        if abs_path not in self.watched_roots:
            raise ValueError(f"Path not monitored: {path}")
            
        logger.info(f"Removing root: {abs_path}")
        self.watched_roots.remove(abs_path)
        
        if abs_path in self.watches:
            self.observer.unschedule(self.watches[abs_path])
            del self.watches[abs_path]
            
        self.save_projects()
        asyncio.create_task(self.notify_clients())

    def set_discovery_root(self, path: str):
        self.discovery_root = path
        self.save_projects()

    def get_current_state(self) -> Dict[str, Any]:
        """Scans all watched roots."""
        all_projects_data = []
        parser = TaskParser()

        # Create a snapshot to iterate safely
        current_roots = list(self.watched_roots)

        for root in current_roots:
            # Check if exists before scanning to avoid crashing if deleted externally
            if not os.path.exists(root):
                continue

            scanner = DirectoryScanner(root)
            projects_meta = scanner.scan()
            
            for meta in projects_meta:
                parsed = parser.parse_file(meta['task_file'])
                all_projects_data.append({
                    "name": meta['name'],
                    "path": meta['path'],
                    "stats": parsed['stats'],
                    "tasks": parsed['tasks'],
                    "links": parsed.get('links', [])
                })
        
        all_projects_data.sort(key=lambda x: x['name'])
        
        return {"projects": all_projects_data}

    async def notify_clients(self):
        logger.info("Changes detected or Root added. Broadcasting update...")
        state = self.get_current_state()
        await self.connection_manager.broadcast(state)

# Initialize Global Manager
project_manager = ProjectManager()

@app.post("/api/projects/create")
async def create_project(
    parent_path: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(None)
):
    try:
        # Validate inputs
        if not parent_path or not name:
            raise HTTPException(status_code=400, detail="Parent path and project name are required")
            
        parent = Path(parent_path)
        if not parent.exists() or not parent.is_dir():
            raise HTTPException(status_code=400, detail="Invalid parent directory")
            
        # Create project directory
        project_path = parent / name
        if project_path.exists():
            raise HTTPException(status_code=400, detail="project name exist")
            
        os.makedirs(project_path)
        
        # Save task.md (or create default)
        file_path = project_path / "task.md"
        if file:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            # Create default empty template
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {name}\n\n- [ ] Initial Task")
            
        # Register project
        # We add the specific project path as a root
        project_manager.add_root(str(project_path))
        
        return {"status": "success", "path": str(project_path), "message": f"Project '{name}' created successfully"}
        
    except Exception as e:
        # Cleanup if created but failed later (optional, but good practice)
        # For now, just report error
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/upload")
async def upload_project_file(
    project_path: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        if not project_path:
            raise HTTPException(status_code=400, detail="Project path required")
            
        path = Path(project_path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        # Save file (overwrite enabled)
        file_path = path / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"status": "success", "message": f"File '{file.filename}' uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CommandRequest(BaseModel):
    path: str
    cmd: str # 'open' or 'dev'

@app.post("/api/projects/command")
async def run_project_command(request: CommandRequest):
    try:
        path = Path(request.path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        if request.cmd == "open":
            # Windows: start Antigravity explicitly
            logger.info(f"Opening Antigravity in {path}")
            os.system(f'cd /d "{path}" && antigravity .')
            return {"status": "success", "message": "Antigravity opened"}
            
        elif request.cmd == "dev":
            # Windows: start dev in a NEW terminal window and keep it open
            logger.info(f"Starting dev server in {path}")
            
            # Check for start.bat
            dev_cmd = "npm run dev"
            if (path / "start.bat").exists():
                logger.info(f"Found start.bat in {path}, using it instead of default dev command")
                dev_cmd = "start.bat"
                
            # we use start cmd /k to open a new window and keep it open if it crashes/ends
            os.system(f'start cmd /k "cd /d \u0022{path}\u0022 && {dev_cmd}"')
            return {"status": "success", "message": f"Dev server started with '{dev_cmd}' in new window"}
            
        else:
            raise HTTPException(status_code=400, detail="Unknown command")
            
    except Exception as e:
        logger.error(f"Error running command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    project_manager.start_watcher()
    if args and args.root:
        try:
            project_manager.add_root(args.root)
        except Exception as e:
            logger.error(f"Failed to add initial root: {e}")

@app.on_event("shutdown")
def shutdown_event():
    project_manager.stop_watcher()

# --- API Endpoints ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await project_manager.connection_manager.connect(websocket)
    try:
        await websocket.send_json(project_manager.get_current_state())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        project_manager.connection_manager.disconnect(websocket)

@app.post("/api/roots")
async def add_root_path(request: RootPathRequest):
    try:
        project_manager.add_root(request.path)
        return {"status": "success", "watched_roots": list(project_manager.watched_roots)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except Exception as e:
        logger.error(f"Error adding root: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/roots")
async def remove_root_path(path: str, delete_files: bool = False):
    try:
        abs_path = os.path.abspath(path)
        # Perform logical removal first
        project_manager.remove_root(path)
        
        # Optionally perform physical removal
        if delete_files:
            if os.path.exists(abs_path):
                logger.warning(f"Physically deleting directory: {abs_path}")
                shutil.rmtree(abs_path)
            else:
                logger.error(f"Cannot delete non-existent path: {abs_path}")
                
        return {"status": "success", "deleted_files": delete_files}
    except ValueError:
         raise HTTPException(status_code=404, detail="Path not found in watchlist")
    except Exception as e:
        logger.error(f"Error removing root: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    return {
        "discovery_root": project_manager.discovery_root,
        "watched_roots": list(project_manager.watched_roots)
    }

@app.post("/api/discover")
async def discover_projects(request: RootPathRequest):
    """
    Scans a directory (shallowly) for potential projects.
    Returns a list of found projects but does NOT add them to the watcher.
    """
    try:
        path = os.path.abspath(request.path)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Directory not found")
            
        # Update discovery root preference
        project_manager.set_discovery_root(path)

        scanner = DirectoryScanner(path, max_depth=1)
        projects = scanner.scan()
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error discovering projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="Initial root directory to scan")
    parsed_args, _ = parser.parse_known_args()
    args = parsed_args
    
    # If running directly, we might need to patch uvicorn run to use this 'app' instance
    # keeping global args accessible.
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # Uvicorn worker mode
    # We need a way to pass args if run via command line, usually via ENV
    # For now, default args to None
    args = None
    # If we want to support --root via uvicorn command line args, it's tricky.
    # We'll assume the API is the primary way to add roots dynamically, 
    # or rely on hardcoded default for dev.
