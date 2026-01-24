import logging
import asyncio
import argparse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Relative imports or Absolute imports depending on execution context.
# Assuming running "python main.py" from backend/ directory.
from app.api.router import api_router
from app.api.endpoints.websocket import router as ws_router
from app.core.globals import get_project_manager

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TaskMancer.Main")

# Lifespan Events (Replaces on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up ProjectWatcher...")
    manager = get_project_manager()
    manager.start_watcher()
    
    # [v13.1] 自動維護：啟動時清理超過 7 天的舊日誌，防止 DB 膨脹
    try:
        manager.db_manager.cleanup_old_data(days=7)
    except Exception as e:
        logger.error(f"Startup DB maintenance failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ProjectWatcher...")
    manager.stop_watcher()
    manager.db_manager.close() # [v13.0] Close DB connection

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
# API Routes (Projects, System, etc.)
app.include_router(api_router, prefix="/api")

# WebSocket Route (Must be at root /ws to match previous behavior)
app.include_router(ws_router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
