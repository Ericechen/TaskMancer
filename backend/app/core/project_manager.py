import asyncio
import logging
import os
import json
import psutil
import time
from pathlib import Path
from typing import Set, Dict, Any, List, Optional
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
from app.utils.lifecycle_logger import log as life_log

logger = logging.getLogger("TaskMancer.Manager")

class ProjectManager:
    """
    專案管理器 (核心控制器)。
    [v13.6] 效能最佳化：新增多級快取與延遲掃描。
    """
    def __init__(self):
        self.watched_roots: Set[str] = set()
        self.connection_manager = ConnectionManager()
        self.observer = Observer()
        self.event_handler: Optional[DebouncedEventHandler] = None
        self.config_file = "projects.json"
        
        # 快取體系
        self.project_meta_cache: Dict[str, Dict] = {} # norm_path -> meta
        self.data_cache: Dict[str, Dict] = {} # norm_path -> {data, timestamp}
        self.system_state_cache = None
        self.system_state_timestamp = 0
        
        self.discovery_root = ""
        self.watches = {} 
        self.active_processes: Dict[str, RunningProcess] = {} 
        
        self.self_path = self._normalize_path(str(Path(__file__).parents[3]))
        self.db_manager = DatabaseManager()
        # [v13.15] Async Mutex Locks for Project Operations
        # 防止針對同一專案的並發 Start/Stop 導致狀態競爭
        self.project_locks: Dict[str, asyncio.Lock] = {}
        psutil.cpu_percent(interval=None)

    def _normalize_path(self, path: str) -> str:
        if not path: return ""
        return os.path.abspath(path).lower().replace("\\", "/")

    def get_lock(self, path: str) -> asyncio.Lock:
        if path not in self.project_locks:
            self.project_locks[path] = asyncio.Lock()
        return self.project_locks[path]

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
                self.discovery_root = data.get('discovery_root', "")
                for path in data.get('roots', []): 
                    self.add_root(path, save=False)
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

    async def get_current_state(self, force_refresh: bool = False) -> Dict[str, Any]:
        """[v13.6] 智慧型全域狀態獲取，帶有 3 秒快取機制"""
        now = time.time()
        if not force_refresh and self.system_state_cache and (now - self.system_state_timestamp < 3):
            return self.system_state_cache

        all_projects_data = []
        parser = TaskParser()
        current_roots = list(self.watched_roots)

        async def scan_root(root):
            root_projects = []
            scanner = DirectoryScanner(root)
            # 快取掃描結果，除非強制重新整理
            projects_meta = await scanner.scan_async(batch_size=100)
            
            for meta in projects_meta:
                norm_path = self._normalize_path(meta['path'])
                self.project_meta_cache[norm_path] = meta
                
                # 使用單個專案獲取邏輯
                p_data = await self.get_project_data_by_path(norm_path, parser=parser)
                if p_data:
                    root_projects.append(p_data)
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

        self.system_state_cache = {"projects": all_projects_data, "system": system_stats}
        self.system_state_timestamp = now
        return self.system_state_cache

    async def get_project_data_by_path(self, path: str, parser: TaskParser = None) -> Optional[Dict[str, Any]]:
        """[v13.6] 帶快取的專案詳細數據獲取"""
        norm_path = self._normalize_path(path)
        now = time.time()
        
        # 1 秒內的高頻請求直接回傳快取
        if norm_path in self.data_cache and (now - self.data_cache[norm_path]['ts'] < 1):
             return self.data_cache[norm_path]['data']

        meta = self.project_meta_cache.get(norm_path)
        if not meta:
            task_md = os.path.join(path, "task.md")
            if not os.path.exists(task_md): return None
            meta = {"name": os.path.basename(path), "path": path, "task_file": task_md, "tags": []}
            self.project_meta_cache[norm_path] = meta

        if not parser: parser = TaskParser()
        parsed = await parser.parse_file_async(meta['task_file'])
        path_obj = Path(meta['path'])
        
        # 基礎資訊
        try:
            all_files = os.listdir(path_obj)
            files_lower = [f.lower() for f in all_files]
            has_start_bat = 'start.bat' in files_lower
            has_readme = any(f.startswith('readme') for f in files_lower)
        except: has_start_bat = has_readme = False

        config_path = os.path.join(path_obj, "config.md")
        has_config = os.path.exists(config_path)
        p_config = ConfigParser.parse_file(config_path) if has_config else {}
        
        # [v13.6] 效能核心：Git 與 Health 分開快取或按需讀取
        git_helper = GitHelper(meta['path'])
        health_report = get_project_health_report(meta['path'])
        live_report = await get_live_report_async(meta['path'], explicit_ports=p_config.get('explicit_ports'))
        
        proc = self.active_processes.get(norm_path)
        
        res = {
            "name": meta['name'],
            "path": norm_path,
            "tags": meta.get('tags', []),
            "stats": parsed['stats'],
            "tasks": parsed['tasks'],
            "links": p_config.get('links') or parsed.get('links', []), 
            "depends_on": [d.strip() for d in p_config.get('depends_on', [])],
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
                "stats": proc.stats if proc else None,
                "history": {"cpu": list(proc.cpu_history), "ram": list(proc.ram_history)} if proc else {"cpu":[], "ram":[]},
                "has_error": proc.has_error if proc else False
            }
        }
        self.data_cache[norm_path] = {'data': res, 'ts': now}
        return res

    async def notify_clients(self, patch_path: str = None, force_metrics_paths: set = None):
        # [v13.23] 修復：只移除真正被 stop 過的進程 (_stop_requested=True)
        # 避免誤刪還在啟動中的進程 (is_running=False 但 _stop_requested=False)
        stopped_paths = [
            path for path, proc in self.active_processes.items() 
            if not proc.is_running and proc._stop_requested
        ]
        for path in stopped_paths:
            if path != self.self_path: # 保護自我監控
                del self.active_processes[path]

        # [v13.9] Watcher Structural Changes Handling
        if force_metrics_paths:
            for raw_path in force_metrics_paths:
                norm = self._normalize_path(raw_path)
                if norm in self.data_cache: del self.data_cache[norm]
                if norm in self.project_meta_cache: del self.project_meta_cache[norm]

        if patch_path:
            norm_patch = self._normalize_path(patch_path)
            # 強制清除快取以確保獲取真正的最新狀態
            if norm_patch in self.data_cache: 
                del self.data_cache[norm_patch]
            
            p_data = await self.get_project_data_by_path(norm_patch)
            if p_data:
                await self.connection_manager.broadcast({"type": "project_patch", "project": p_data})
                
                # 重新計算系統統計 (基於清理後的 active_processes)
                all_procs = self.active_processes.values()
                active_procs = [p for p in all_procs if p.is_running and p.stats]
                
                sum_cpu = sum(p.stats['cpu'] for p in active_procs)
                sum_ram = sum(p.stats['ram'] for p in active_procs)
                total_ram = psutil.virtual_memory().total / (1024 * 1024)
                
                await self.connection_manager.broadcast({
                    "type": "system_stats", 
                    "system": {
                        "cpu_percent": round(sum_cpu, 1),
                        "ram_percent": round((sum_ram / total_ram) * 100, 2),
                        "ram_total_gb": round(total_ram / 1024, 1),
                        "active_count": len([p for p in all_procs if p.is_running])
                    }
                })
                return
        
        # 全域更新時也要清除全域快取
        self.system_state_cache = None
        state = await self.get_current_state(force_refresh=True) # Force refresh on global notify
        await self.connection_manager.broadcast(state)

    async def start_project(self, target_path: Path, trigger: str = "manual", visited: Set[str] = None):
        n_path = self._normalize_path(str(target_path))
        
        # [v13.28] Cycle Detection
        if visited is None: visited = set()
        if n_path in visited:
            logger.info(f"Circular dependency detected (skipped): {n_path}")
            return
        visited.add(n_path)
        
        # [v13.15] Critical State Lock
        async with self.get_lock(n_path):
            # [v13.14] Strict State Lock (Anti-Race Condition)
            # 如果該專案正在停止中，絕對禁止啟動，防止停止過程中的競爭請求
            if n_path in self.active_processes:
                proc = self.active_processes[n_path]
                if proc.alert_level == 'stopping':
                    logger.warning(f"BLOCKED START: {n_path} is currently stopping. Trigger: {trigger}")
                    return 

            # [v13.22] 統一生命週期追蹤
            life_log("PROJECT_MANAGER", f"START_PROJECT (trigger={trigger})", n_path)

            logger.info(f"REQUEST START: {n_path} (Trigger: {trigger})")

            if n_path == self.self_path: return

            # [v13.24] 啟動中防護：同時檢查 is_running 和 alert_level
            if n_path in self.active_processes:
                proc = self.active_processes[n_path]
                if proc.is_running:
                    logger.info(f"SKIP START: {n_path} is already running.")
                    return
                if proc.alert_level == 'starting':
                    logger.info(f"SKIP START: {n_path} is already starting.")
                    return

            c_path = target_path / "config.md"
            p_config = ConfigParser.parse_file(str(c_path)) if c_path.exists() else {}
            deps = p_config.get('depends_on', [])

            if deps:
                for d_name in [d.strip() for d in deps]:
                    dep_path = next((p for p, m in self.project_meta_cache.items() if m['name'].lower() == d_name.lower() or p == self._normalize_path(d_name)), None)
                    if dep_path:
                        # [v13.14] Dependency Loop Protection
                        # 防止 A -> B, B -> A 無限循環啟動
                        # 只有當依賴項完全沒在運行時才啟動
                        is_run = dep_path in self.active_processes and self.active_processes[dep_path].is_running
                        if not is_run:
                            # Check recursively if dependency is stopping
                             if dep_path in self.active_processes and self.active_processes[dep_path].alert_level == 'stopping':
                                 logger.info(f"SKIP DEP START: {d_name} is stopping.")
                                 continue
                             
                             logger.info(f"AUTO-START Dependency: {d_name} for {target_path.name}")
                             # Recursive call will form its own lock check
                             await self.start_project(Path(dep_path), trigger=f"dep_of_{target_path.name}", visited=visited)

            proc = RunningProcess(n_path, target_path.name, self.connection_manager, db_manager=self.db_manager)
            self.active_processes[n_path] = proc
            abs_bat = os.path.abspath(os.path.join(str(target_path), "start.bat"))
            if os.path.exists(abs_bat):
                # [v13.19] 廣播 starting 狀態，讓前端鎖定 switch
                proc.alert_level = 'starting'
                await self.connection_manager.broadcast({
                    "type": "process_stats",
                    "path": n_path,
                    "stats": None,
                    "alert_level": "starting",
                    "history": {"cpu": [], "ram": []}
                })
                
                # [v13.26] 從 config 取得 health check port
                e_vars = ConfigParser.get_env_vars(str(c_path)) if c_path.exists() else {}
                health_port = None
                if p_config.get('explicit_ports'):
                    health_port = p_config['explicit_ports'][0]['port']
                    logger.info(f"Health check port for {target_path.name}: {health_port}")
                
                await proc.start(f'"{abs_bat}"', {**e_vars, "CI": "true"}, health_check_port=health_port)
                # [v13.7] 立即讓全域快取失效並廣播
                self.system_state_cache = None
                asyncio.create_task(self.notify_clients(patch_path=n_path))

    async def stop_project(self, path: Path) -> Dict[str, str]:
        norm_path = self._normalize_path(str(path))
        
        # [v13.22] 詳細追蹤
        life_log("PROJECT_MANAGER", "STOP_PROJECT", norm_path, f"process_active={norm_path in self.active_processes}")
        
        # [v13.15] Critical State Lock
        async with self.get_lock(norm_path):
            if norm_path in self.data_cache: del self.data_cache[norm_path]
            self.system_state_cache = None

            if norm_path == self.self_path: return {"status": "error", "message": "Self-Protection active."}
            
            if norm_path in self.active_processes:
                proc = self.active_processes[norm_path]
                
                # [v13.24] 重複停止防護
                if proc.alert_level == 'stopping':
                    logger.info(f"SKIP STOP: {norm_path} is already stopping.")
                    return {"status": "skipped", "message": "Already stopping."}
                
                # 1. 廣播 "Stopping" 狀態
                proc.alert_level = 'stopping'
                await self.connection_manager.broadcast({
                     "type": "process_stats",
                     "path": norm_path,
                     "stats": proc.stats,
                     "alert_level": "stopping",
                     "history": {"cpu": list(proc.cpu_history), "ram": list(proc.ram_history)}
                })
                
                # 2. 執行停止 (觸發 taskkill)
                proc.stop()
                
                # 3. [v13.13] 強制等待並驗證進程死亡
                is_dead = await proc.wait_for_death()
                
                if is_dead:
                    # Double check if it's still there (race condition safety)
                    if norm_path in self.active_processes:
                        del self.active_processes[norm_path]
                    
                    await self.connection_manager.broadcast({
                        "type": "log_status", "project": proc.name, "path": proc.project_path, "status": "stopped"
                    })
                    await self.notify_clients() # 全局刷新
                    return {"status": "success", "message": "Stopped."}
                else:
                    # [v13.25] 即使進程沒死掉，也要從 active_processes 移除
                    # 這樣用戶可以重試啟動（taskkill 已經執行過了）
                    if norm_path in self.active_processes:
                        del self.active_processes[norm_path]
                    
                    await self.connection_manager.broadcast({
                        "type": "log_status", "project": proc.name, "path": proc.project_path, "status": "stopped"
                    })
                    await self.notify_clients()
                    return {"status": "warning", "message": "Process may still be running (zombie). Retry if needed."}

            return {"status": "not_running", "message": "Not running."}
