import asyncio
import argparse
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

# Global State
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

manager = ConnectionManager()
args = None
observer = None

def get_current_state() -> Dict[str, Any]:
    """Scans and parses all projects to generate the current state."""
    scanner = DirectoryScanner(args.root)
    projects_meta = scanner.scan()
    
    parser = TaskParser()
    projects_data = []
    
    for meta in projects_meta:
        parsed = parser.parse_file(meta['task_file'])
        projects_data.append({
            "name": meta['name'],
            "path": meta['path'],
            "stats": parsed['stats'],
            "tasks": parsed['tasks']
        })
        
    return {"projects": projects_data}

async def notify_clients():
    """Callback triggered by Watcher."""
    logger.info("Changes detected. Broadcasting update...")
    state = get_current_state()
    await manager.broadcast(state)

@app.on_event("startup")
async def startup_event():
    global observer
    
    # Initialize Watcher
    logger.info(f"Starting watcher on root: {args.root}")
    event_handler = DebouncedEventHandler(
        loop=asyncio.get_running_loop(),
        callback=notify_clients,
        debounce_seconds=0.5
    )
    
    observer = Observer()
    observer.schedule(event_handler, args.root, recursive=True)
    observer.start()

@app.on_event("shutdown")
def shutdown_event():
    if observer:
        observer.stop()
        observer.join()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state immediately
        await websocket.send_json(get_current_state())
        
        while True:
            # Keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    
    # Parse CLI Args manually if running directly, 
    # but Uvicorn usually runs the app object.
    # To support `python main.py --root X`, we need a wrapper or handle it globally.
    # For simplicity, we use argparse here and set it to global `args`.
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parsed_args, _ = parser.parse_known_args()
    args = parsed_args # Set global
    
    # Note: When running via `uvicorn main:app`, this block isn't executed, 
    # and `args` will be None. We need a way to pass args.
    # PROPER WAY: Read Environment Variable or Default to '.' if args is None.
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # If running via uvicorn command line, we default to current directory 
    # or need a pattern to inject configuration.
    # Let's fallback to "current working directory" if args is None.
    if args is None:
        import sys
        # Trivial mock for args
        class Args:
            root = "." 
        args = Args()
