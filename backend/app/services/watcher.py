import asyncio
import time
import logging
from typing import Callable, Set
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger("TaskMancer.Watcher")

class DebouncedEventHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, callback: Callable[[Set[str]], None], debounce_seconds: float = 0.5):
        self.loop = loop
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._last_event_time = 0
        self._scheduled_handle = None
        self._structural_changes: Set[str] = set()

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return

        path = event.src_path.replace("\\", "/")
        
        # v10.0.1: 特殊處理 Git 變更 - 僅允許核心狀態檔案觸發
        if '/.git/' in path:
            # 必須精確匹配核心檔案，排除 .lock 等暫存檔
            important_git_files = ['/.git/index', '/.git/HEAD', '/.git/FETCH_HEAD', '/.git/config']
            if not any(path.endswith(f) for f in important_git_files):
                return
        
        # 增加 .lock 檔案過濾
        ignore_patterns = [
            '/node_modules/', '/__pycache__/', '/.venv/', '/venv/', 
            'projects.json', 'taskmancer.db', '.db-journal', '.db-wal',
            '.tmp', '.swp', '.lock'
        ]
        
        if any(p in path for p in ignore_patterns):
            return

        logger.info(f"Triggered by: {path} ({event.event_type})")
        
        # 如果是檔案建立或刪除，標記為結構性變更，需要重新整理 Metrics (v10.3)
        if event.event_type in ['created', 'deleted', 'moved']:
            self._structural_changes.add(event.src_path)
            
        self.debounce()

    def debounce(self):
        current_time = time.time()
        self._last_event_time = current_time

        if self._scheduled_handle:
            self._scheduled_handle.cancel()

        self._scheduled_handle = self.loop.call_later(self.debounce_seconds, self.trigger_callback)

    def trigger_callback(self):
        # Capture the changes and reset
        structural_copy = set(self._structural_changes)
        self._structural_changes.clear()
        self._scheduled_handle = None
        
        logger.info(f"Debounce finished, structural changes: {len(structural_copy)}")
        
        if asyncio.iscoroutinefunction(self.callback):
            asyncio.create_task(self.callback(force_metrics_paths=structural_copy))
        else:
            self.callback(force_metrics_paths=structural_copy)
