import os

content = """import asyncio
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
    \"\"\"
    專案管理器 (核心控制器)。
    負責：
    1. 監控檔案系統變更 (Watchdog)。
    2. 掃描與解析專案結構 (Parser)。
    3. 管理 WebSocket 連線與廣播 (ConnectionManager)。
    4. 管理子進程的生命週期 (RunningProcess)。
    5. 維護系統全域狀態。
    \"\"\"
    def __init__(self):
        \"\"\"
        初始化 ProjectManager。
        設定路徑、資料庫連線、觀察者與狀態快取。
        \"\"\"
        self.watched_roots: Set[str] = set()
        self.connection_manager = ConnectionManager()
        self.observer = Observer()
        self.event_handler: Optional[DebouncedEventHandler] = None
        self.config_file = \"projects.json\"
        self.discovery_root = \"\"
        self.watches = {} # Map path -> ObservedWatch
        self.metrics_cache = {} # path -> metrics_data
        self.dirty_metrics = set() # paths that need metrics re-scan
        self.active_processes: Dict[str, RunningProcess] = {} # normalized path -> RunningProcess
        
        # 計算 TaskMancer 根目錄 (假設位於 app/core/project_manager.py 的上三層)
        self.self_path = self._normalize_path(str(Path(__file__).parents[3]))
        
        self.db_manager = DatabaseManager()
        # 初始化 CPU 追蹤 (首次調用返回 0)
        psutil.cpu_percent(interval=None)

    def _normalize_path(self, path: str) -> str:
        \"\"\"
        標準化路徑以保持 Windows 下的一致性。
        轉為小寫並使用正斜線。
        \"\"\"
        if not path: return \"\"
        return os.path.abspath(path).lower().replace(\"\\\\\", \"/\")

    def start_watcher(self):
        \"\"\"
        啟動檔案系統監控器與事件處理迴圈。
        \"\"\"
        loop = asyncio.get_running_loop()
        self.event_handler = DebouncedEventHandler(
            loop=loop,
            callback=self.notify_clients,
            debounce_seconds=0.5
        )
        self.observer.start()
        
        # [v11.2] 自我監控注入 (靜默模式)
        self.inject_self_monitoring(loop)
        
        self.load_projects()

    def inject_self_monitoring(self, loop):
        \"\"\"
        允許 TaskMancer 監控自身的資源消耗與日誌。
        \"\"\"
        try:
            logger.info(f\"Injecting self-monitoring for TaskMancer at {self.self_path}\")
            proc = RunningProcess(self.self_path, \"TaskMancer (Self)\", self.connection_manager, db_manager=self.db_manager)
            
            proc.is_running = True
            
            try:
                class MockSubprocess:
                    def __init__(self, pid): self.pid = pid
                proc.process = MockSubprocess(os.getpid())
                
                asyncio.create_task(proc.monitor_resources())
                
                class WSHandler(logging.Handler):
                    def emit(self, record):
                        log_entry = self.format(record)
                        def send():
                            asyncio.create_task(proc.connection_manager.broadcast({
                                \"type\": \"log\",
                                \"project\": \"TaskMancer (Self)\",
                                \"path\": proc.project_path,
                                \"content\": log_entry
                            }))
                        loop.call_soon_threadsafe(send)
                
                ws_h = WSHandler()
                ws_h.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
                logging.getLogger().addHandler(ws_h)
                
                self.active_processes[self.self_path] = proc
                
                async def heartbeat():
                    while proc.is_running:
                        await proc.connection_manager.broadcast({
                            \"type\": \"log\",
                            \"project\": \"TaskMancer (Self)\",
                            \"path\": proc.project_path,
                            \"content\": \"\\033[90m[TELEMETRY] System health heartbeat active...\\033[0m\"
                        })
                        await asyncio.sleep(60)

                loop.call_later(2.0, lambda: asyncio.create_task(proc.connection_manager.broadcast({
                    \"type\": \"log\",
                    \"project\": \"TaskMancer (Self)\",
                    \"path\": proc.project_path,
                    \"content\": \"\\033[1;32m[SYSTEM] TaskMancer Self-Intelligence Monitoring Online\\033[0m\"
                })))
                asyncio.create_task(heartbeat())
            except Exception as e:
                logger.error(f\"Failed to attach self-monitor: {e}\")
        except Exception as e:
            logger.error(f\"Self-monitoring injection failed: {e}\")

    def stop_watcher(self):
        \"\"\"
        停止檔案系統監控器。
        \"\"\"
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def load_projects(self):
        \"\"\"
        從 projects.json 設定檔載入專案根目錄。
        \"\"\"
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paths = data.get('roots', [])
                self.discovery_root = data.get('discovery_root', \"\")
                logger.info(f\"Loading {len(paths)} projects from config. Discovery Root: {self.discovery_root}\")
                for path in paths:
                    try:
                        self.add_root(path, save=False)
                    except Exception as e:
                        logger.error(f\"Failed to load project {path}: {e}\")
        except Exception as e:
            logger.error(f\"Error loading config: {e}\")

    def save_projects(self):
        \"\"\"
        將當前監控的根目錄與設定儲存至 projects.json。
        \"\"\"
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    \"roots\": list(self.watched_roots),
                    \"discovery_root\": self.discovery_root
                }, f, indent=2)
            logger.info(\"Projects configuration saved.\")
        except Exception as e:
            logger.error(f\"Error saving config: {e}\")

    def add_root(self, path: str, save: bool = True):
        \"\"\"
        新增一個監控根目錄。
        \"\"\"
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f\"Path does not exist: {path}\")

        if abs_path in self.watched_roots:
            return # Already watched

        logger.info(f\"Adding root: {abs_path}\")
        self.watched_roots.add(abs_path)
        
        if self.event_handler:
            watch = self.observer.schedule(self.event_handler, abs_path, recursive=True)
            self.watches[abs_path] = watch
        
        if save:
            self.save_projects()
            asyncio.create_task(self.notify_clients())

    def remove_root(self, path: str):
        \"\"\"
        移除一個監控根目錄。
        \"\"\"
        abs_path = os.path.abspath(path)
        if abs_path not in self.watched_roots:
            raise ValueError(f\"Path not monitored: {path}\")
            
        logger.info(f\"Removing root: {abs_path}\")
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
        \"\"\"
        設定專案探索的根路徑。
        \"\"\"
        self.discovery_root = path
        self.save_projects()

    async def get_current_state(self, force_metrics_paths: Set[str] = None) -> Dict[str, Any]:
        \"\"\"
        非同步掃描所有監控根目錄，並返回完整的專案與系統狀態。
        \"\"\"
        all_projects_data = []
        parser = TaskParser()

        current_roots = list(self.watched_roots)

        async def scan_root(root):
            root_projects = []
            if not os.path.exists(root):
                return []
            
            scanner = DirectoryScanner(root)
            projects_meta = await scanner.scan_async(batch_size=100)
            
            for meta in projects_meta:
                try:
                    project_path = meta['path']
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

                    config_path = os.path.join(path_obj, \"config.md\")
                    has_config = os.path.exists(config_path)
                    project_config = ConfigParser.parse_file(config_path) if has_config else {}
                    final_links = project_config.get('links') or parsed.get('links', [])

                    git_helper = GitHelper(project_path)
                    git_snapshot = git_helper.get_repo_snapshot()
                    git_momentum = git_helper.get_momentum_score()
                    
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
                    
                    try:
                        live_report = await get_live_report_async(
                            project_path, 
                            explicit_ports=project_config.get('explicit_ports')
                        )
                    except Exception as e:
                        logger.error(f\"Live report failed for {meta['name']}: {e}\")
                        live_report = {\"active_ports\": [], \"dependency_audit\": {\"status\": \"error\"}}

                    proc = self.active_processes.get(norm_path)

                    root_projects.append({
                        \"name\": meta['name'],
                        \"path\": norm_path, # [v13.3] Standardized path
                        \"tags\": meta.get('tags', []),
                        \"stats\": parsed['stats'],
                        \"tasks\": parsed['tasks'],
                        \"links\": final_links, 
                        \"depends_on\": project_config.get('depends_on', []),
                        \"hasConfig\": has_config,
                        \"hasStartBat\": has_start_bat,
                        \"hasReadme\": has_readme,
                        \"git\": git_snapshot,
                        \"momentum\": git_momentum,
                        \"health\": health_report['health'],
                        \"metrics\": health_report['metrics'],
                        \"live\": live_report,
                        \"process\": {
                            \"is_running\": proc.is_running if proc else False,
                            \"alert_level\": proc.alert_level if proc else \"normal\",
                            \"stats\": proc.stats if proc else None,
                            \"has_error\": proc.has_error if proc else False,
                            \"history\": {
                                \"cpu\": list(proc.cpu_history),
                                \"ram\": list(proc.ram_history)
                            } if proc else {\"cpu\": [], \"ram\": []}
                        }
                    })
                except Exception as e:
                    logger.error(f\"Failed to process project {meta['name']}: {e}\")
                    continue
            return root_projects

        results = await asyncio.gather(*(scan_root(r) for r in current_roots), return_exceptions=True)
        for r_list in results:
            if isinstance(r_list, Exception):
                logger.error(f\"Root scan failed: {r_list}\")
                continue
            all_projects_data.extend(r_list)
            
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
            \"cpu_percent\": round(sum_cpu, 1),
            \"ram_percent\": round((sum_ram_mb / total_ram_mb) * 100, 2),
            \"ram_used_gb\": round(sum_ram_mb / 1024, 2),
            \"ram_total_gb\": round(total_ram_mb / 1024, 1),
            \"active_count\": active_count
        }

        return {
            \"projects\": all_projects_data,
            \"system\": system_stats
        }

    async def get_project_data_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        \"\"\"
        掃描並返回單個專案的數據 (用於 Delta Updates 增量更新)。
        \"\"\"
        abs_path = os.path.abspath(path)
        found_meta = None
        for root in self.watched_roots:
            scanner = DirectoryScanner(root)
            projects_meta = await scanner.scan_async(batch_size=10)
            meta = next((m for m in projects_meta if self._normalize_path(m['path']) == self._normalize_path(abs_path)), None)
            if meta:
                found_meta = meta
                break
        
        if not found_meta: return None
        
        parser = TaskParser()
        parsed = await parser.parse_file_async(found_meta['task_file'])
        path_obj = Path(abs_path)
        
        try:
            all_files = os.listdir(path_obj)
            files_lower = [f.lower() for f in all_files]
            has_start_bat = 'start.bat' in files_lower
            has_readme = any(f.startswith('readme') for f in files_lower)
        except:
            has_start_bat = has_readme = False

        config_path = os.path.join(path_obj, \"config.md\")
        has_config = os.path.exists(config_path)
        project_config = ConfigParser.parse_file(config_path) if has_config else {}
        final_links = project_config.get('links') or parsed.get('links', [])

        git_helper = GitHelper(abs_path)
        health_report = get_project_health_report(abs_path)
        live_report = await get_live_report_async(abs_path, explicit_ports=project_config.get('explicit_ports'))
        
        norm_path = self._normalize_path(abs_path)
        proc = self.active_processes.get(norm_path)
        
        cpu_hist = list(proc.cpu_history) if proc else []
        ram_hist = list(proc.ram_history) if proc else []
        alert_lvl = proc.alert_level if proc else \"normal\"
        
        if not cpu_hist and self.db_manager:
            db_h = self.db_manager.get_recent_metrics(norm_path)
            cpu_hist = db_h['cpu']
            ram_hist = db_h['ram']

        return {
            \"name\": found_meta['name'],
            \"path\": norm_path, # [v13.3] Standardized path
            \"tags\": found_meta.get('tags', []),
            \"stats\": parsed['stats'],
            \"tasks\": parsed['tasks'],
            \"links\": final_links, 
            \"depends_on\": project_config.get('depends_on', []),
            \"hasConfig\": has_config,
            \"hasStartBat\": has_start_bat,
            \"hasReadme\": has_readme,
            \"git\": git_helper.get_repo_snapshot(),
            \"momentum\": git_helper.get_momentum_score(),
            \"health\": health_report['health'],
            \"metrics\": health_report['metrics'],
            \"live\": live_report,
            \"process\": {
                \"is_running\": proc.is_running if proc else False,
                \"alert_level\": alert_lvl,
                \"stats\": proc.stats if proc else None,
                \"has_error\": proc.has_error if proc else False,
                \"history\": {
                    \"cpu\": cpu_hist,
                    \"ram\": ram_hist
                }
            }
        }

    async def notify_clients(self, force_metrics_paths: Set[str] = None, patch_path: str = None):
        \"\"\"
        通知所有連接的 WebSocket 客戶端系統狀態更新。
        \"\"\"
        if patch_path:
            p_data = await self.get_project_data_by_path(patch_path)
            if p_data:
                await self.connection_manager.broadcast({
                    \"type\": \"project_patch\",
                    \"project\": p_data
                })
                # [v13.3] 優化：略過全量掃描，直接發送現有的系統統計
                all_procs = self.active_processes.values()
                sum_cpu = sum(p.stats['cpu'] for p in all_procs if p.is_running and p.stats)
                sum_ram = sum(p.stats['ram'] for p in all_procs if p.is_running and p.stats)
                total_ram = psutil.virtual_memory().total / (1024 * 1024)
                
                await self.connection_manager.broadcast({
                    \"type\": \"system_stats\", 
                    \"system\": {
                        \"cpu_percent\": round(sum_cpu, 1),
                        \"ram_percent\": round((sum_ram / total_ram) * 100, 2),
                        \"ram_total_gb\": round(total_ram / 1024, 1),
                        \"active_count\": sum(1 for p in all_procs if p.is_running)
                    }
                })
                return

        state = await self.get_current_state(force_metrics_paths=force_metrics_paths)
        await self.connection_manager.broadcast(state)

    async def start_project(self, target_path: Path):
        \"\"\"
        遞迴啟動專案及其依賴項 (depends_on)。
        \"\"\"
        n_path = self._normalize_path(str(target_path))
        if n_path == self.self_path: return

        # 1. 解析依賴關係
        c_path = target_path / \"config.md\"
        p_config = ConfigParser.parse_file(str(c_path)) if c_path.exists() else {}
        deps = p_config.get('depends_on', [])

        # 2. 鏈式啟動依賴
        if deps:
            logger.info(f\"Checking dependencies for {target_path.name}: {deps}\")
            all_projects = await self.get_current_state()
            for dep_name_or_path in deps:
                dep_proj = next((p for p in all_projects['projects'] if p['name'] == dep_name_or_path or self._normalize_path(p['path']) == self._normalize_path(dep_name_or_path)), None)
                if dep_proj:
                    dep_norm = self._normalize_path(dep_proj['path'])
                    is_running = dep_norm in self.active_processes and self.active_processes[dep_norm].is_running
                    if not is_running:
                        logger.info(f\"Auto-starting dependency: {dep_proj['name']}\")
                        await self.start_project(Path(dep_proj['path']))

        # 3. 啟動目標專案
        if n_path in self.active_processes and self.active_processes[n_path].is_running:
            return 

        p_name = target_path.name
        e_vars = ConfigParser.get_env_vars(str(c_path)) if c_path.exists() else {}

        proc = RunningProcess(n_path, p_name, self.connection_manager, db_manager=self.db_manager)
        self.active_processes[n_path] = proc
        
        abs_bat = os.path.abspath(os.path.join(str(target_path), \"start.bat\"))
        if os.path.exists(abs_bat):
            await proc.start(f'\"{abs_bat}\"', {**e_vars, \"CI\": \"true\"})
            logger.info(f\"Started project: {p_name}\")
            # [v13.3] 立即通知前端狀態變更
            asyncio.create_task(self.notify_clients(patch_path=n_path))

    def stop_project(self, path: Path) -> Dict[str, str]:
        \"\"\"
        停止指定路徑的專案。
        \"\"\"
        norm_path = self._normalize_path(str(path))
        if norm_path == self.self_path:
            return {\"status\": \"error\", \"message\": \"Cannot stop TaskMancer core via dashboard (Self-Protection).\"}

        if norm_path in self.active_processes:
            proc = self.active_processes[norm_path]
            proc.stop()
            del self.active_processes[norm_path]
            asyncio.create_task(self.notify_clients())
            return {\"status\": \"success\", \"message\": \"Process stopped and cleaned up\"}
        return {\"status\": \"not_running\", \"message\": \"No active process for this path\"}
\"\"\"

with open(\"backend/app/core/project_manager.py\", \"w\", encoding=\"utf-8\") as f:
    f.write(content)
"

with open("fix_pm_final.py", "w", encoding="utf-8") as f:
    f.write(content)
