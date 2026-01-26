import asyncio
import logging
import os
import json
import shutil
import psutil
from pathlib import Path
from typing import Set, Dict, Any, List, Optional
from collections import deque
from watchdog.observers import Observer

# Internal Imports
from app.core.websocket import ConnectionManager
from app.core.db_manager import DatabaseManager
from app.core.process import RunningProcess
from app.services.scanner import DirectoryScanner
from app.services.watcher import DebouncedEventHandler
from app.parsers.task_parser import TaskParser
from app.parsers.config_parser import ConfigParser
from app.utils.git_utils import GitHelper
from app.utils.health_utils import get_project_health_report
from app.utils.live_utils import get_live_report_async

logger = logging.getLogger("TaskMancer.Manager")

class ProjectManager:
    """
    專案管理器 (核心控制器)。
    """
    def __init__(self):
        self.watched_roots: Set[str] = set()
        self.connection_manager = ConnectionManager()
        self.observer = Observer()
        self.event_handler: Optional[DebouncedEventHandler] = None
        self.config_file = "projects.json"
        self.discovery_root = ""
        self.watches = {} 
        self.metrics_cache = {} 
        self.dirty_metrics = set() 
        self.active_processes: Dict[str, RunningProcess] = {} 
        self.project_meta_cache: Dict[str, Dict] = {} # norm_path -> meta_data (name, tags, task_file)
        
        self.self_path = self._normalize_path(str(Path(__file__).parents[3]))
        self.db_manager = DatabaseManager()
        psutil.cpu_percent(interval=None)

    def _normalize_path(self, path: str) -> str:
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
        self.inject_self_monitoring(loop)
        self.load_projects()

    def inject_self_monitoring(self, loop):
        try:
            logger.info(f"Injecting self-monitoring for TaskMancer at {self.self_path}")
            proc = RunningProcess(self.self_path, "TaskMancer (Self)", self.connection_manager, db_manager=self.db_manager)
            proc.is_running = True
            
            class MockSubprocess:
                def __init__(self, pid): self.pid = pid
            proc.process = MockSubprocess(os.getpid())
            
            asyncio.create_task(proc.monitor_resources())
            
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
            logger.error(f"Self-monitoring failed: {e}")

    def stop_watcher(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def load_projects(self):
        if not os.path.exists(self.config_file): return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paths = data.get('roots', [])
                self.discovery_root = data.get('discovery_root', "")
                for path in paths: self.add_root(path, save=False)
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def save_projects(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({"roots": list(self.watched_roots), "discovery_root": self.discovery_root}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def add_root(self, path: str, save: bool = True):
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path): raise FileNotFoundError(f"Path does not exist: {path}")
        if abs_path in self.watched_roots: return
        self.watched_roots.add(abs_path)
        if self.event_handler:
            watch = self.observer.schedule(self.event_handler, abs_path, recursive=True)
            self.watches[abs_path] = watch
        if save:
            self.save_projects()
            asyncio.create_task(self.notify_clients())

    def remove_root(self, path: str):
        abs_path = os.path.abspath(path)
        if abs_path not in self.watched_roots: raise ValueError(f"Path not monitored: {path}")
        self.watched_roots.remove(abs_path)
        if abs_path in self.watches:
            try: self.observer.unschedule(self.watches[abs_path])
            except: pass
            del self.watches[abs_path]
        self.save_projects()
        asyncio.create_task(self.notify_clients())

    async def get_current_state(self, force_metrics_paths: Set[str] = None) -> Dict[str, Any]:
        all_projects_data = []
        parser = TaskParser()
        current_roots = list(self.watched_roots)

        async def scan_root(root):
            root_projects = []
            if not os.path.exists(root): return []
            scanner = DirectoryScanner(root)
            projects_meta = await scanner.scan_async(batch_size=100)
            
            for meta in projects_meta:
                try:
                    project_path = meta['path']
                    norm_path = self._normalize_path(project_path)
                    self.project_meta_cache[norm_path] = meta # Update meta cache

                    path_obj = Path(project_path)
                    if not path_obj.exists(): continue
                    parsed = await parser.parse_file_async(meta['task_file'])
                    
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

                    git_helper = GitHelper(project_path)
                    git_snapshot = git_helper.get_repo_snapshot()
                    git_momentum = git_helper.get_momentum_score()
                    
                    should_refresh_metrics = (
                        norm_path not in self.metrics_cache or 
                        (force_metrics_paths and norm_path in force_metrics_paths) or
                        norm_path in self.dirty_metrics
                    )

                    if should_refresh_metrics:
                        health_report = get_project_health_report(project_path)
                        self.metrics_cache[norm_path] = health_report
                        if norm_path in self.dirty_metrics: self.dirty_metrics.remove(norm_path)
                    else:
                        health_report = self.metrics_cache[norm_path]
                    
                    live_report = await get_live_report_async(project_path, explicit_ports=project_config.get('explicit_ports'))
                    proc = self.active_processes.get(norm_path)

                    root_projects.append({
                        "name": meta['name'],
                        "path": norm_path,
                        "tags": meta.get('tags', []),
                        "stats": parsed['stats'],
                        "tasks": parsed['tasks'],
                        "links": final_links, 
                        "depends_on": [d.strip() for d in project_config.get('depends_on', [])],
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
                            "alert_level": proc.alert_level if proc else "normal",
                            "stats": proc.stats if proc else None,
                            "has_error": proc.has_error if proc else False,
                            "history": {
                                "cpu": list(proc.cpu_history),
                                "ram": list(proc.ram_history)
                            } if proc else {"cpu": [], "ram": []}
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to process project {meta.get('name')}: {e}")
            return root_projects

        results = await asyncio.gather(*(scan_root(r) for r in current_roots), return_exceptions=True)
        for r_list in results:
            if isinstance(r_list, list): all_projects_data.extend(r_list)
            
        mem_info = psutil.virtual_memory()
        total_ram_mb = mem_info.total / (1024 * 1024)
        sum_cpu = sum(p['process']['stats']['cpu'] for p in all_projects_data if p['process']['is_running'] and p['process']['stats'])
        sum_ram_mb = sum(p['process']['stats']['ram'] for p in all_projects_data if p['process']['is_running'] and p['process']['stats'])
        
        system_stats = {
            "cpu_percent": round(sum_cpu, 1),
            "ram_percent": round((sum_ram_mb / total_ram_mb) * 100, 2),
            "ram_used_gb": round(sum_ram_mb / 1024, 2),
            "ram_total_gb": round(total_ram_mb / 1024, 1),
            "active_count": sum(1 for p in all_projects_data if p['process']['is_running'])
        }

        return {"projects": all_projects_data, "system": system_stats}

    async def get_project_data_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        abs_path = os.path.abspath(path)
        norm_path = self._normalize_path(abs_path)
        
        # [v13.4] Optimize: Check meta cache first, otherwise fall back to scanning the folder directly
        meta = self.project_meta_cache.get(norm_path)
        if not meta:
            task_md = os.path.join(abs_path, "task.md")
            if not os.path.exists(task_md): return None
            # Minimal meta for fallback
            meta = {"name": os.path.basename(abs_path), "path": abs_path, "task_file": task_md, "tags": []}

        parser = TaskParser()
        parsed = await parser.parse_file_async(meta['task_file'])
        path_obj = Path(abs_path)
        
        try:
            all_files = os.listdir(path_obj)
            files_lower = [f.lower() for f in all_files]
            has_start_bat = 'start.bat' in files_lower
            has_readme = any(f.startswith('readme') for f in files_lower)
        except: has_start_bat = has_readme = False

        config_path = os.path.join(path_obj, "config.md")
        has_config = os.path.exists(config_path)
        project_config = ConfigParser.parse_file(config_path) if has_config else {}
        final_links = project_config.get('links') or parsed.get('links', [])

        git_helper = GitHelper(abs_path)
        health_report = get_project_health_report(abs_path)
        live_report = await get_live_report_async(abs_path, explicit_ports=project_config.get('explicit_ports'))
        
        proc = self.active_processes.get(norm_path)
        cpu_hist = list(proc.cpu_history) if proc else []
        ram_hist = list(proc.ram_history) if proc else []
        
        if not cpu_hist and self.db_manager:
            db_h = self.db_manager.get_recent_metrics(norm_path)
            cpu_hist = db_h['cpu']
            ram_hist = db_h['ram']

        return {
            "name": meta['name'],
            "path": norm_path,
            "tags": meta.get('tags', []),
            "stats": parsed['stats'],
            "tasks": parsed['tasks'],
            "links": final_links, 
            "depends_on": [d.strip() for d in project_config.get('depends_on', [])],
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
                "alert_level": proc.alert_level if proc else "normal",
                "stats": proc.stats if proc else None,
                "has_error": proc.has_error if proc else False,
                "history": {"cpu": cpu_hist, "ram": ram_hist}
            }
        }

    async def notify_clients(self, force_metrics_paths: Set[str] = None, patch_path: str = None):
        if patch_path:
            p_data = await self.get_project_data_by_path(patch_path)
            if p_data:
                await self.connection_manager.broadcast({"type": "project_patch", "project": p_data})
                all_procs = self.active_processes.values()
                sum_cpu = sum(p.stats['cpu'] for p in all_procs if p.is_running and p.stats)
                sum_ram = sum(p.stats['ram'] for p in all_procs if p.is_running and p.stats)
                total_ram = psutil.virtual_memory().total / (1024 * 1024)
                await self.connection_manager.broadcast({
                    "type": "system_stats", 
                    "system": {
                        "cpu_percent": round(sum_cpu, 1),
                        "ram_percent": round((sum_ram / total_ram) * 100, 2),
                        "ram_total_gb": round(total_ram / 1024, 1),
                        "active_count": sum(1 for p in all_procs if p.is_running)
                    }
                })
                return
        state = await self.get_current_state(force_metrics_paths=force_metrics_paths)
        await self.connection_manager.broadcast(state)

    async def start_project(self, target_path: Path):
        n_path = self._normalize_path(str(target_path))
        if n_path == self.self_path: return

        c_path = target_path / "config.md"
        p_config = ConfigParser.parse_file(str(c_path)) if c_path.exists() else {}
        deps = p_config.get('depends_on', [])

        if deps:
            # [v13.4] Case-insensitive dependency lookup
            all_state = await self.get_current_state()
            for d_name in deps:
                d_name = d_name.strip()
                dep_proj = next((p for p in all_state['projects'] if p['name'].lower() == d_name.lower() or self._normalize_path(p['path']) == self._normalize_path(d_name)), None)
                if dep_proj:
                    dep_norm = self._normalize_path(dep_proj['path'])
                    is_run = dep_norm in self.active_processes and self.active_processes[dep_norm].is_running
                    if not is_run:
                        await self.start_project(Path(dep_proj['path']))

        if n_path in self.active_processes and self.active_processes[n_path].is_running: return 

        proc = RunningProcess(n_path, target_path.name, self.connection_manager, db_manager=self.db_manager)
        self.active_processes[n_path] = proc
        abs_bat = os.path.abspath(os.path.join(str(target_path), "start.bat"))
        if os.path.exists(abs_bat):
            e_vars = ConfigParser.get_env_vars(str(c_path)) if c_path.exists() else {}
            await proc.start(f'"{abs_bat}"', {**e_vars, "CI": "true"})
            asyncio.create_task(self.notify_clients(patch_path=n_path))

    def stop_project(self, path: Path) -> Dict[str, str]:
        norm_path = self._normalize_path(str(path))
        if norm_path == self.self_path: return {"status": "error", "message": "Self-Protection active."}
        if norm_path in self.active_processes:
            proc = self.active_processes[norm_path]
            proc.stop()
            # [v13.5] Force immediate UI update
            asyncio.create_task(self.connection_manager.broadcast({
                "type": "log_status",
                "project": proc.name,
                "path": proc.project_path,
                "status": "stopped"
            }))
            # Do not delete immediately, let the monitor/log loops handle cleanup
            asyncio.create_task(self.notify_clients())
            return {"status": "success", "message": "Stopped."}
        return {"status": "not_running", "message": "Not running."}
