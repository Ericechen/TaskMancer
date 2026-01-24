import os
import shutil
import logging
from fastapi import APIRouter, HTTPException
from app.core.globals import get_project_manager
from app.schemas import RootPathRequest

router = APIRouter()
logger = logging.getLogger("TaskMancer.API.System")

@router.get("/config")
async def get_config():
    """
    獲取當前系統配置 (如探索根目錄)。
    """
    manager = get_project_manager()
    return {"discovery_root": manager.discovery_root}

@router.get("/roots")
async def get_roots():
    """
    獲取所有監控的根目錄列表。
    """
    manager = get_project_manager()
    return {"roots": list(manager.watched_roots)}

@router.post("/roots")
async def add_root(request: RootPathRequest):
    """
    新增監控根目錄。
    """
    manager = get_project_manager()
    try:
        manager.add_root(request.path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/roots")
async def remove_root(path: str, delete_files: bool = False):
    """
    移除監控根目錄。
    
    Args:
        delete_files (bool): 是否同時從硬碟刪除檔案 (危險操作)。
    """
    manager = get_project_manager()
    try:
        abs_path = os.path.abspath(path)
        manager.remove_root(abs_path)
        
        if delete_files and os.path.exists(abs_path):
            logger.info(f"Deleting project files: {abs_path}")
            shutil.rmtree(abs_path)
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
