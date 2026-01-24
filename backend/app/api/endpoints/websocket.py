import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.globals import get_project_manager

router = APIRouter()
logger = logging.getLogger("TaskMancer.API.WebSocket")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端點。
    處理實時系統狀態推送與日誌串流。
    """
    manager = get_project_manager()
    await manager.connection_manager.connect(websocket)
    try:
        # 發送初始狀態
        state = await manager.get_current_state()
        await websocket.send_json(state)
        
        while True:
            await websocket.receive_text() # 保持連線活躍
    except WebSocketDisconnect:
        manager.connection_manager.disconnect(websocket)
    except Exception as e:
        # [v13.2] 忽略常見的連線關閉錯誤，避免 Error Log 刷屏
        if "Cannot call" in str(e) or "closed" in str(e):
            logger.info(f"WebSocket closed (client disconnect): {e}")
        else:
            logger.error(f"WebSocket error: {e}")
        manager.connection_manager.disconnect(websocket)
