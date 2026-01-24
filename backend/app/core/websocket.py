import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("TaskMancer.WebSocket")

class ConnectionManager:
    """
    WebSocket 連線管理器。
    負責追蹤活躍連線並提供廣播功能。
    """
    def __init__(self):
        """
        初始化連接列表。
        """
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        接受新的 WebSocket 連線並加入管理列表。
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        移除已斷開的 WebSocket 連線。
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        向所有活躍連線廣播 JSON 訊息。
        若發送失敗則自動移除該連線。
        """
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                # [v13.2] 連線中斷屬正常現象，使用 Info/Warning 級別即可
                logger.warning(f"Client dropped during broadcast: {e}")
                if connection in self.active_connections:
                    self.active_connections.remove(connection)
