from fastapi import APIRouter
from app.api.endpoints import projects, system

api_router = APIRouter()

api_router.include_router(system.router, tags=["system"]) # roots are at /api/roots
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
