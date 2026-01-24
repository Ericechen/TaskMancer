import os
import shutil
import logging
import asyncio
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, File, UploadFile, Form

from app.core.globals import get_project_manager
from app.schemas import CommandRequest

router = APIRouter()
logger = logging.getLogger("TaskMancer.API.Projects")

@router.get("/readme")
async def get_project_readme(path: str):
    """
    獲取指定專案的 README.md 內容。
    不區分大小寫。

    Args:
        path (str): 專案路徑。
    """
    try:
        project_path = Path(path)
        if not project_path.exists() or not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        # 不區分大小寫搜尋 README
        readme_file = next((f for f in os.listdir(project_path) if f.lower() == 'readme.md'), None)
        if not readme_file:
            raise HTTPException(status_code=404, detail="README.md not found")
            
        with open(project_path / readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading README: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_project_logs(path: str, limit: int = 500):
    """
    從資料庫獲取指定專案的歷史日誌。
    
    Args:
        path (str): 專案路徑。
        limit (int): 返回的最大行數。
    """
    manager = get_project_manager()
    try:
        norm_path = manager._normalize_path(path)
        logs = manager.db_manager.get_recent_logs(norm_path, limit=limit)
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error fetching logs from DB: {e}")
        return {"logs": []}

@router.post("/action")
async def run_project_action(request: CommandRequest):
    """
    執行專案操作 (啟動/停止/開啟 Antigravity)。
    
    Args:
        request.path (str): 目標專案路徑。
        request.action (str): 操作類型 ('start.bat', 'stop', 'antigravity...')
    """
    manager = get_project_manager()
    try:
        path = Path(request.path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        if request.action.startswith("antigravity"):
            # Windows: 顯式啟動 Antigravity
            logger.info(f"Opening Antigravity in {path}")
            os.system(f'cd /d "{path}" && antigravity .')
            return {"status": "success", "message": "Antigravity opened"}
            
        if request.action == "start.bat":
            await manager.start_project(path)
            return {"status": "success", "message": "Project and dependencies starting..."}
            
        elif request.action == "stop":
            return manager.stop_project(path)

        else:
            raise HTTPException(status_code=400, detail="Unknown action")
            
    except Exception as e:
        logger.error(f"Error running action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_project_files(path: str = Form(...), files: List[UploadFile] = File(...)):
    """
    上傳檔案至指定專案目錄。
    
    Args:
        path (str): 目標目錄路徑。
        files (List[UploadFile]): 檔案列表。
    """
    manager = get_project_manager()
    try:
        target_path = Path(path)
        if not target_path.exists() or not target_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")
            
        for file in files:
            file_path = target_path / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # 觸發重新掃描通知
        asyncio.create_task(manager.notify_clients())
        return {"status": "success", "uploaded": len(files)}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
