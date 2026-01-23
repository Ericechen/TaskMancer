import asyncio
import time
import logging
from typing import Callable, Set
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger("TaskMancer.Watcher")

class DebouncedEventHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, callback: Callable[[str], None], debounce_seconds: float = 0.5):
        self.loop = loop
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._last_event_time = 0
        self._scheduled_handle = None
        self._changed_paths: Set[str] = set()

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return

        path = event.src_path.replace("\\", "/")
        
        # v10.0.1: 特殊處理 Git 變更，允許 Index 或 Head 變更觸發刷新
        # 排除掉其他的 git 內部雜訊
        if '/.git/' in path:
            if not any(important in path for important in ['/.git/index', '/.git/HEAD', '/.git/FETCH_HEAD']):
                return
        
        ignore_patterns = ['/node_modules/', '/__pycache__/', '/.venv/', '/venv/', 'projects.json', '.tmp', '.swp']
        
        if any(p in path for p in ignore_patterns):
            return

        logger.info(f"Triggered by: {path}")
        self._changed_paths.add(event.src_path)
        self.debounce()

    def debounce(self):
        current_time = time.time()
        self._last_event_time = current_time

        if self._scheduled_handle:
            self._scheduled_handle.cancel()

        self._scheduled_handle = self.loop.call_later(self.debounce_seconds, self.trigger_callback)

    def trigger_callback(self):
        # This runs on the event loop
        # We can clear the changed paths and invoke the callback
        self._changed_paths.clear() # Reset
        self._scheduled_handle = None
        logger.info("Debounce finished, triggering update...")
        
        # Fire and forget (or await if callback is async, but call_later expects synchronous function, 
        # so we might need to create task if callback is async)
        if asyncio.iscoroutinefunction(self.callback):
            asyncio.create_task(self.callback())
        else:
            self.callback()
