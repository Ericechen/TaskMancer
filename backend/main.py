import logging
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

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup / Shutdown Events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up ProjectWatcher...")
    get_project_manager().start_watcher()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ProjectWatcher...")
    get_project_manager().stop_watcher()

# Include Routers
# API Routes (Projects, System, etc.)
app.include_router(api_router, prefix="/api")

# WebSocket Route (Must be at root /ws to match previous behavior)
app.include_router(ws_router)
