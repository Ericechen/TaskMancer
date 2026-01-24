import asyncio
import argparse
import logging
import os
import shutil
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any, Set
from collections import deque
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
from db_manager import DatabaseManager

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
    def __init__(self, project_path: str, name: str, connection_manager, db_manager: DatabaseManager = None):
        # [v11.2] Force normalize for consistent lookup
        self.project_path = project_path.lower().replace("\\", "/")
        self.name = name
        self.process = None
        self.connection_manager = connection_manager
        self.db_manager = db_manager
        self.is_running = False
        self.stats = {"cpu": 0, "ram": 0}
        self.has_error = False
        self.alert_level = "normal" # normal, warning, critical
        # Metrics History (v11.0) - Keep last 300 samples (~5-10 mins)
        self.cpu_history = deque(maxlen=300)
        self.ram_history = deque(maxlen=300)

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
            asyncio.create_task(self.monitor_resources())
            logger.info(f"Started managed process for {self.name} (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start process for {self.name}: {e}")

    async def monitor_resources(self):
        try:
            p = psutil.Process(self.process.pid)
            while self.is_running:
                try:
                    cpu_percent = 0
                    memory_bytes = 0
                    
                    children = p.children(recursive=True)
                    for child in [p] + children:
                        try:
                            # interval=None means non-blocking, uses time since last call
                            cpu_percent += child.cpu_percent(interval=None)
                            memory_bytes += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                            
                    self.stats = {
                        "cpu": round(cpu_percent, 1),
                        "ram": round(memory_bytes / (1024 * 1024), 1) # MB
                    }
                    
                    # [v12.0] Threshold Alert System
                    new_alert = "normal"
                    if self.stats["cpu"] > 80 or self.stats["ram"] > 1024:
                        new_alert = "warning"
                    if self.stats["cpu"] > 95 or self.stats["ram"] > 2048:
                        new_alert = "critical"
                    
                    self.alert_level = new_alert

                    # Update History
                    self.cpu_history.append(self.stats["cpu"])
                    self.ram_history.append(self.stats["ram"])
                    
                    # [v12.0] Persistence
                    if self.db_manager:
                        self.db_manager.store_metric(self.project_path, self.stats["cpu"], self.stats["ram"])

                    await self.connection_manager.broadcast({
                        "type": "process_stats",
                        "path": self.project_path,
                        "stats": self.stats,
                        "alert_level": self.alert_level,
                        "history": {
                            "cpu": list(self.cpu_history),
                            "ram": list(self.ram_history)
                        }
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Resource monitoring failed for {self.name}: {e}")

    async def read_logs(self):
        logger.info(f"Log reader started for {self.name} (PID: {self.process.pid})")
        error_keywords = ['error', 'failed', 'exception', 'critical', 'err:', 'fatal']
        
        while self.is_running:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    logger.info(f"Log stream reached EOF for {self.name}")
                    break
                
                text = line.decode('utf-8', errors='ignore').rstrip()
                if text:
                    # Error detection (v10.4)
                    lower_text = text.lower()
                    if any(kw in lower_text for kw in error_keywords):
                        if not self.has_error:
                            self.has_error = True
                            await self.connection_manager.broadcast({
                                "type": "process_error",
                                "path": self.project_path,
                                "has_error": True
                            })

                    logger.info(f"[{self.name}] {text}")
                    
                    # [v12.0] Persistence
                    if self.db_manager:
                        self.db_manager.store_log(self.project_path, text)

                    await self.connection_manager.broadcast({
                        "type": "log",
                        "project": self.name,
                        "path": self.project_path,
                        "content": text
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
            try:
                # Use psutil to clean up the entire process tree
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            except Exception as e:
                logger.error(f"Stop process failed: {e}")
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
        self.active_processes: Dict[str, RunningProcess] = {} # normalized path -> RunningProcess
        self.self_path = self._normalize_path(str(Path(__file__).parent.parent))
        self.db_manager = DatabaseManager()
        # Initialize CPU tracking (first call returns 0)
        psutil.cpu_percent(interval=None)

    def _normalize_path(self, path: str) -> str:
        """Normalize path for Windows consistency."""
        if not path: return ""
        return os.path.abspath(path).lower().replace("\\", "/")

    def start_watcher(self):
        loop = asyncio.get_running_loop()
        self.event_handler = DebouncedEventHandler(
            loop=loop,
            callback=self.notify_clients,
            debounce_seconds=0.5
        )
        self.observer.start()
        
        # [v11.2] Self-Monitoring Injection (Silent)
        self.inject_self_monitoring(loop)
        
        self.load_projects()

    def inject_self_monitoring(self, loop):
        """Allows TaskMancer to monitor its own resources and logs."""
        try:
            logger.info(f"Injecting self-monitoring for TaskMancer at {self.self_path}")
            proc = RunningProcess(self.self_path, "TaskMancer (Self)", self.connection_manager, db_manager=self.db_manager)
            
            proc.is_running = True
            
            import psutil
            try:
                class MockSubprocess:
                    def __init__(self, pid): self.pid = pid
                proc.process = MockSubprocess(os.getpid())
                
                asyncio.create_task(proc.monitor_resources())
                
                # Setup Thread-Safe Logging Redirect
                class WSHandler(logging.Handler):
                    def emit(self, record):
                        log_entry = self.format(record)
                        def send():
                            asyncio.create_task(proc.connection_manager.broadcast({
                                "type": "log",
                                "project": "TaskMancer (Self)",
                                "path": proc.project_path,
                                "content": log_entry
                            }))
                        loop.call_soon_threadsafe(send)
                
                ws_h = WSHandler()
                ws_h.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
                logging.getLogger().addHandler(ws_h)
                
                self.active_processes[self.self_path] = proc
                
                # [v11.2] Immediate Feedback Log + Heartbeat
                async def heartbeat():
                    while proc.is_running:
                        await proc.connection_manager.broadcast({
                            "type": "log",
                            "project": "TaskMancer (Self)",
                            "path": proc.project_path,
                            "content": "\033[90m[TELEMETRY] System health heartbeat active...\033[0m"
                        })
                        await asyncio.sleep(60)

                loop.call_later(2.0, lambda: asyncio.create_task(proc.connection_manager.broadcast({
                    "type": "log",
                    "project": "TaskMancer (Self)",
                    "path": proc.project_path,
                    "content": "\033[1;32m[SYSTEM] TaskMancer Self-Intelligence Monitoring Online\033[0m"
                })))
                asyncio.create_task(heartbeat())
            except Exception as e:
                logger.error(f"Failed to attach self-monitor: {e}")
        except Exception as e:
            logger.error(f"Self-monitoring injection failed: {e}")

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
                    norm_path = self._normalize_path(project_path)
                    should_refresh_metrics = (
                        norm_path not in self.metrics_cache or 
                        (force_metrics_paths and norm_path in force_metrics_paths) or
                        norm_path in self.dirty_metrics
                    )

                    if should_refresh_metrics:
                        health_report = get_project_health_report(project_path)
                        self.metrics_cache[norm_path] = health_report
                        if norm_path in self.dirty_metrics:
                            self.dirty_metrics.remove(norm_path)
                    else:
                        health_report = self.metrics_cache[norm_path]
                    
                    # Async Live Status with Explicit Ports (Safe Mode)
                    try:
                        live_report = await get_live_report_async(
                            project_path, 
                            explicit_ports=project_config.get('explicit_ports')
                        )
                    except Exception as e:
                        logger.error(f"Live report failed for {meta['name']}: {e}")
                        live_report = {"active_ports": [], "dependency_audit": {"status": "error"}}

                    norm_path = self._normalize_path(project_path)
                    proc = self.active_processes.get(norm_path)

                    root_projects.append({
                        "name": meta['name'],
                        "path": project_path,
                        "tags": meta.get('tags', []), # [v11.0] Critical Fix
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
                        "live": live_report,
                        "process": {
                            "is_running": proc.is_running if proc else False,
                            "stats": proc.stats if proc else None,
                            "has_error": proc.has_error if proc else False,
                            "history": {
                                "cpu": list(proc.cpu_history),
                                "ram": list(proc.ram_history)
                            } if proc else {"cpu": [], "ram": []}
                        }
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
            
        # [v11.2] Sum metrics from all active projects (not global OS)
        sum_cpu = 0
        sum_ram_mb = 0
        active_count = 0
        
        for p in all_projects_data:
            if p['process']['is_running'] and p['process']['stats']:
                sum_cpu += p['process']['stats']['cpu']
                sum_ram_mb += p['process']['stats']['ram']
                active_count += 1
        
        mem_info = psutil.virtual_memory()
        total_ram_mb = mem_info.total / (1024 * 1024)
        
        system_stats = {
            "cpu_percent": round(sum_cpu, 1),
            "ram_percent": round((sum_ram_mb / total_ram_mb) * 100, 2), # % based on total system RAM
            "ram_used_gb": round(sum_ram_mb / 1024, 2),
            "ram_total_gb": round(total_ram_mb / 1024, 1),
            "active_count": active_count
        }

        return {
            "projects": all_projects_data,
            "system": system_stats
        }

    async def get_project_data_by_path(self, path: str) -> Dict[str, Any]:
        """Scans and returns data for a single project (for Delta Updates)."""
        abs_path = os.path.abspath(path)
        # Find which root it belongs to
        found_meta = None
        for root in self.watched_roots:
            scanner = DirectoryScanner(root)
            meta = next((m for m in scanner.scan() if self._normalize_path(m['path']) == self._normalize_path(abs_path)), None)
            if meta:
                found_meta = meta
                break
        
        if not found_meta: return None
        
        parser = TaskParser()
        parsed = parser.parse_file(found_meta['task_file'])
        path_obj = Path(abs_path)
        
        try:
            all_files = os.listdir(path_obj)
            files_lower = [f.lower() for f in all_files]
            has_start_bat = 'start.bat' in files_lower
            has_readme = any(f.startswith('readme') for f in files_lower)
        except:
            has_start_bat = has_readme = False

        config_path = os.path.join(path_obj, "config.md")
        has_config = os.path.exists(config_path)
        project_config = ConfigParser.parse_file(config_path) if has_config else {}
        final_links = project_config.get('links') or parsed.get('links', [])

        git_helper = GitHelper(abs_path)
        health_report = get_project_health_report(abs_path)
        live_report = await get_live_report_async(abs_path, explicit_ports=project_config.get('explicit_ports'))
        
        norm_path = self._normalize_path(abs_path)
        proc = self.active_processes.get(norm_path)
        
        # [v12.0] History Restoration from DB
        cpu_hist = list(proc.cpu_history) if proc else []
        ram_hist = list(proc.ram_history) if proc else []
        alert_lvl = proc.alert_level if proc else "normal"
        
        if not cpu_hist and self.db_manager:
            db_h = self.db_manager.get_recent_metrics(norm_path)
            cpu_hist = db_h['cpu']
            ram_hist = db_h['ram']

        return {
            "name": found_meta['name'],
            "path": abs_path,
            "tags": found_meta.get('tags', []),
            "stats": parsed['stats'],
            "tasks": parsed['tasks'],
            "links": final_links, 
            "hasConfig": has_config,
            "hasStartBat": has_start_bat,
            "hasReadme": has_readme,
            "git": git_helper.get_repo_snapshot(),
            "momentum": git_helper.get_momentum_score(),
            "health": health_report['health'],
            "metrics": health_report['metrics'],
            "live": live_report,
            "process": {
                "is_running": proc.is_running if proc else False,
                "alert_level": alert_lvl,
                "stats": proc.stats if proc else None,
                "has_error": proc.has_error if proc else False,
                "history": {
                    "cpu": cpu_hist,
                    "ram": ram_hist
                }
            }
        }

    async def notify_clients(self, force_metrics_paths: Set[str] = None, patch_path: str = None):
        if patch_path:
            # [v12.0] Delta Update
            p_data = await self.get_project_data_by_path(patch_path)
            if p_data:
                await self.connection_manager.broadcast({
                    "type": "project_patch",
                    "project": p_data
                })
                # We still need to update system stats for everyone
                state = await self.get_current_state()
                await self.connection_manager.broadcast({"type": "system_stats", "system": state['system']})
                return

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

@app.get("/api/projects/logs")
async def get_project_logs(path: str, limit: int = 500):
    try:
        norm_path = project_manager._normalize_path(path)
        logs = project_manager.db_manager.get_recent_logs(norm_path, limit=limit)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error fetching logs from DB: {e}")
        return {"logs": []}

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
            norm_path = project_manager._normalize_path(str(path))
            if norm_path == project_manager.self_path:
                return {"status": "error", "message": "TaskMancer is already running (Self-Managed)."}
                
            # Managed Start with Log Streaming (v10.3)
            logger.info(f"Managed start request for: {path}")
            
            # Check if already running
            if norm_path in project_manager.active_processes:
                proc = project_manager.active_processes[norm_path]
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

            proc = RunningProcess(norm_path, project_name, project_manager.connection_manager)
            project_manager.active_processes[norm_path] = proc
            
            # Execute start.bat with explicit path and CI environment
            abs_bat_path = os.path.abspath(os.path.join(str(path), "start.bat"))
            await proc.start(f'"{abs_bat_path}"', {**env_vars, "CI": "true"})
            
            return {"status": "success", "message": "Process started with streaming logs"}
            
        elif request.action == "stop":
            norm_path = project_manager._normalize_path(str(path))
            if norm_path == project_manager.self_path:
                return {"status": "error", "message": "Cannot stop TaskMancer core via dashboard (Self-Protection)."}

            if norm_path in project_manager.active_processes:
                proc = project_manager.active_processes[norm_path]
                proc.stop()
                # Remove from tracking pool immediately
                del project_manager.active_processes[norm_path]
                # Broadcast updated state to all clients
                asyncio.create_task(project_manager.notify_clients())
                return {"status": "success", "message": "Process stopped and cleaned up"}
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
