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
        # We only care about file events, not directory events (usually)
        # and specifically we are interested in task.md changes.
        # But atomic saves often involve rename/delete/create.
        # So we should track the affected paths.
        
        if event.is_directory:
            return

        filename = event.src_path.split('\\')[-1].split('/')[-1]
        
        # Simple filter: only care if it looks related to task.md or temp files that might become task.md
        # However, for atomic saves, we might see temporary filenames.
        # So simpler approach: Just debounce EVERYTHING in the watched folder?
        # No, that's too broad. 
        # Better: Triger checking the directory scanner again? 
        # Or simpler: If the path ends with 'task.md', or we detect a move to 'task.md'.
        
        # Let's just track that *something* happened, and then trigger a rescan/reparse of the relevant project
        # In this simplistic version, we just blindly trigger a reload of everything or specific paths.
        # To make it robust for atomic save:
        # vscode writes to .task.md.swp -> rename to task.md
        # so we final destination is what matters.
        
        # If we just watch for ANY change, and then after 500ms quiet period, 
        # we ask the ProjectManager to "Refresh All" or "Refresh Modified".
        
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
