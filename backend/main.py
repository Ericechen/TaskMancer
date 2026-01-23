import asyncio
import argparse
import logging
import os
import shutil
import json
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
from git_utils import GitHelper
from health_utils import get_project_health_report
from live_utils import get_live_report_async
from config_parser import ConfigParser

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

class RunningProcess:
    def __init__(self, project_path: str, name: str, connection_manager):
        self.project_path = project_path
        self.name = name
        self.process = None
        self.connection_manager = connection_manager
        self.is_running = False

    async def start(self, cmd: str, env: dict):
        try:
            import subprocess
            self.process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_path,
                env={**os.environ, **env},
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            self.is_running = True
            asyncio.create_task(self.read_logs())
            logger.info(f"Started managed process for {self.name}")
        except Exception as e:
            logger.error(f"Failed to start process for {self.name}: {e}")

    async def read_logs(self):
        logger.info(f"Log reader started for {self.name}")
        while self.is_running:
            try:
                # Use read() instead of readline() to catch partial lines and handle unusual buffering
                chunk = await self.process.stdout.read(4096)
                if not chunk:
                    logger.info(f"Log stream ended for {self.name}")
                    break
                
                text = chunk.decode('utf-8', errors='ignore')
                lines = text.splitlines()
                
                for line in lines:
                    if line.strip():
                        await self.connection_manager.broadcast({
                            "type": "log",
                            "project": self.name,
                            "path": self.project_path,
                            "content": line
                        })
            except Exception as e:
                logger.error(f"Error reading logs for {self.name}: {e}")
                break
        
        self.is_running = False
        await self.connection_manager.broadcast({
            "type": "log_status",
            "project": self.name,
            "path": self.project_path,
            "status": "stopped"
        })

    def stop(self):
        if self.process:
            import signal
            if os.name == 'nt':
                os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
            else:
                self.process.terminate()
            self.is_running = False

# --- Global State ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

class ProjectManager:
    def __init__(self):
        self.watched_roots: Set[str] = set()
        self.connection_manager = ConnectionManager()
        self.observer = Observer()
        self.event_handler = None
        self.config_file = "projects.json"
        self.discovery_root = ""
        self.watches = {} # Map path -> ObservedWatch
        self.metrics_cache = {} # path -> metrics_data
        self.dirty_metrics = set() # paths that need metrics re-scan
        self.active_processes: Dict[str, RunningProcess] = {} # path -> RunningProcess

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
            try:
                self.observer.unschedule(self.watches[abs_path])
            except:
                pass
            del self.watches[abs_path]
            
        self.save_projects()
        asyncio.create_task(self.notify_clients())

    def set_discovery_root(self, path: str):
        self.discovery_root = path
        self.save_projects()

    async def get_current_state(self, force_metrics_paths: Set[str] = None) -> Dict[str, Any]:
        """Scans all watched roots asynchronously."""
        all_projects_data = []
        parser = TaskParser()

        current_roots = list(self.watched_roots)

        async def scan_root(root):
            root_projects = []
            if not os.path.exists(root):
                return []
            
            scanner = DirectoryScanner(root)
            projects_meta = scanner.scan()
            
            for meta in projects_meta:
                try:
                    project_path = meta['path']
                    path_obj = Path(project_path)
                    parsed = parser.parse_file(meta['task_file'])
                    
                    try:
                        all_files = os.listdir(path_obj)
                        files_lower = [f.lower() for f in all_files]
                        has_start_bat = 'start.bat' in files_lower
                        has_readme = any(f.startswith('readme') for f in files_lower)
                    except:
                        has_start_bat = has_readme = False

                    # Check for config.md (v7.5)
                    config_path = os.path.join(path_obj, "config.md")
                    has_config = os.path.exists(config_path)
                    project_config = ConfigParser.parse_file(config_path) if has_config else {}
                    
                    # Links: config.md (Priority) > task.md (Fallback)
                    final_links = project_config.get('links') or parsed.get('links', [])

                    git_helper = GitHelper(project_path)
                    git_snapshot = git_helper.get_repo_snapshot()
                    git_momentum = git_helper.get_momentum_score()
                    
                    # Metrics Caching (v10.3)
                    should_refresh_metrics = (
                        project_path not in self.metrics_cache or 
                        (force_metrics_paths and project_path in force_metrics_paths) or
                        project_path in self.dirty_metrics
                    )

                    if should_refresh_metrics:
                        health_report = get_project_health_report(project_path)
                        self.metrics_cache[project_path] = health_report
                        if project_path in self.dirty_metrics:
                            self.dirty_metrics.remove(project_path)
                    else:
                        health_report = self.metrics_cache[project_path]
                    
                    # Async Live Status with Explicit Ports (Safe Mode)
                    try:
                        live_report = await get_live_report_async(
                            project_path, 
                            explicit_ports=project_config.get('explicit_ports')
                        )
                    except Exception as e:
                        logger.error(f"Live report failed for {meta['name']}: {e}")
                        live_report = {"active_ports": [], "dependency_audit": {"status": "error"}}

                    root_projects.append({
                        "name": meta['name'],
                        "path": project_path,
                        "stats": parsed['stats'],
                        "tasks": parsed['tasks'],
                        "links": final_links, 
                        "hasConfig": has_config,
                        "hasStartBat": has_start_bat,
                        "hasReadme": has_readme,
                        "git": git_snapshot,
                        "momentum": git_momentum,
                        "health": health_report['health'],
                        "metrics": health_report['metrics'],
                        "live": live_report
                    })
                except Exception as e:
                    logger.error(f"Failed to process project {meta['name']}: {e}")
                    continue
            return root_projects

        results = await asyncio.gather(*(scan_root(r) for r in current_roots), return_exceptions=True)
        for r_list in results:
            if isinstance(r_list, Exception):
                logger.error(f"Root scan failed: {r_list}")
                continue
            all_projects_data.extend(r_list)
            
        return {"projects": all_projects_data}

    async def notify_clients(self, force_metrics_paths: Set[str] = None):
        state = await self.get_current_state(force_metrics_paths=force_metrics_paths)
        await self.connection_manager.broadcast(state)

project_manager = ProjectManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up ProjectWatcher...")
    project_manager.start_watcher()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ProjectWatcher...")
    project_manager.stop_watcher()

# --- API Endpoints ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await project_manager.connection_manager.connect(websocket)
    try:
        # Send initial state
        state = await project_manager.get_current_state()
        await websocket.send_json(state)
        
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        project_manager.connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        project_manager.connection_manager.disconnect(websocket)

@app.get("/api/config")
async def get_config():
    return {"discovery_root": project_manager.discovery_root}

@app.get("/api/roots")
async def get_roots():
    return {"roots": list(project_manager.watched_roots)}

@app.post("/api/roots")
async def add_root(request: RootPathRequest):
    try:
        project_manager.add_root(request.path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/roots")
async def remove_root(path: str, delete_files: bool = False):
    try:
        abs_path = os.path.abspath(path)
        project_manager.remove_root(abs_path)
        
        if delete_files and os.path.exists(abs_path):
            logger.info(f"Deleting project files: {abs_path}")
            shutil.rmtree(abs_path)
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/projects/readme")
async def get_project_readme(path: str):
    try:
        project_path = Path(path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        # Find readme case-insensitively
        readme_file = next((f for f in os.listdir(project_path) if f.lower() == 'readme.md'), None)
        if not readme_file:
            raise HTTPException(status_code=404, detail="README.md not found")
            
        with open(project_path / readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading README: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CommandRequest(BaseModel):
    path: str
    action: str 

@app.post("/api/projects/action")
async def run_project_action(request: CommandRequest):
    try:
        path = Path(request.path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        if request.action.startswith("antigravity"):
            # Windows: start Antigravity explicitly
            logger.info(f"Opening Antigravity in {path}")
            os.system(f'cd /d "{path}" && antigravity .')
            return {"status": "success", "message": "Antigravity opened"}
            
        elif request.action == "start.bat":
            # Managed Start with Log Streaming (v10.3)
            logger.info(f"Managed start request for: {path}")
            
            # Check if already running
            if str(path) in project_manager.active_processes:
                proc = project_manager.active_processes[str(path)]
                if proc.is_running:
                    return {"status": "already_running", "message": "Process is already streaming logs."}

            config_path = path / "config.md"
            env_vars = ConfigParser.get_env_vars(str(config_path)) if config_path.exists() else {}
            
            # Find the project name for logging
            project_name = path.name
            for root in project_manager.watched_roots:
                scanner = DirectoryScanner(root)
                meta = next((m for m in scanner.scan() if m['path'] == str(path)), None)
                if meta:
                    project_name = meta['name']
                    break

            proc = RunningProcess(str(path), project_name, project_manager.connection_manager)
            project_manager.active_processes[str(path)] = proc
            
            # Execute start.bat with explicit path and CI environment
            # Note: create_subprocess_shell on Windows already uses 'cmd /c'
            # We only need to provide the quoted path to the batch file
            abs_bat_path = os.path.abspath(os.path.join(str(path), "start.bat"))
            await proc.start(f'"{abs_bat_path}"', {**env_vars, "CI": "true"})
            
            return {"status": "success", "message": "Process started with streaming logs"}
            
        elif request.action == "stop":
            if str(path) in project_manager.active_processes:
                project_manager.active_processes[str(path)].stop()
                return {"status": "success", "message": "Process stopped"}
            return {"status": "not_running", "message": "No active process for this path"}

        else:
            raise HTTPException(status_code=400, detail="Unknown action")
            
    except Exception as e:
        logger.error(f"Error running action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/upload")
async def upload_project_files(path: str = Form(...), files: List[UploadFile] = File(...)):
    try:
        target_path = Path(path)
        if not target_path.exists() or not target_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        for file in files:
            file_path = target_path / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # Trigger re-scan
        asyncio.create_task(project_manager.notify_clients())
        return {"status": "success", "message": f"Uploaded {len(files)} files"}
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create")
async def create_project(path: str = Form(...), name: str = Form(...), task_file: UploadFile = File(None)):
    try:
        parent_path = Path(path)
        if not parent_path.exists() or not parent_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid parent path")
            
        project_dir = parent_path / name
        os.makedirs(project_dir, exist_ok=True)
        
        # Create or upload task.md
        task_path = project_dir / "task.md"
        if task_file:
            with open(task_path, "wb") as buffer:
                shutil.copyfileobj(task_file.file, buffer)
        else:
            # Generate template if not provided
            with open(task_path, "w", encoding="utf-8") as f:
                f.write(f"# {name} 開發任務清單\n\n## v1.0 - 初始化 (進行中)\n- [ ] 專案初始化\n")
        
        # Auto-track the new project
        project_manager.add_root(str(project_dir))
        
        return {"status": "success", "path": str(project_dir)}
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discover")
async def discover_projects(request: RootPathRequest):
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
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parsed_args, _ = parser.parse_known_args()
    args = parsed_args
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)
else:
    # Uvicorn worker mode
    pass
