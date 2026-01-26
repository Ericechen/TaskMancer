import asyncio
import os
import psutil
import logging
from collections import deque
from typing import TYPE_CHECKING, Dict, Optional, Deque, List, Any

if TYPE_CHECKING:
    from app.core.websocket import ConnectionManager
    from app.core.db_manager import DatabaseManager

logger = logging.getLogger("TaskMancer.Process")

class RunningProcess:
    """
    管理單個正在運行的專案進程。
    負責啟動、停止、資源監控 (CPU/RAM) 以及日誌串流處理。
    """
    def __init__(self, project_path: str, name: str, connection_manager: 'ConnectionManager', db_manager: Optional['DatabaseManager'] = None):
        """
        初始化 RunningProcess 實例。

        Args:
            project_path (str): 專案的絕對路徑。
            name (str): 專案名稱。
            connection_manager (ConnectionManager): 用於廣播 WebSocket 訊息。
            db_manager (Optional[DatabaseManager]): 用於持久化存儲日誌和指標。
        """
        # [v11.2] 強制標準化路徑以保持查找一致性
        self.project_path = project_path.lower().replace("\\", "/")
        self.name = name
        self.process: Optional[asyncio.subprocess.Process] = None
        self.connection_manager = connection_manager
        self.db_manager = db_manager
        self.is_running = False
        self.stats = {"cpu": 0, "ram": 0}
        self.has_error = False
        self.alert_level = "normal" # normal, warning, critical
        # Metrics History (v11.0) - 保留最後 300 個樣本 (~5-10 分鐘)
        self.cpu_history: Deque[float] = deque(maxlen=300)
        self.ram_history: Deque[float] = deque(maxlen=300)

    async def start(self, cmd: str, env: dict):
        """
        異步啟動子進程。

        Args:
            cmd (str): 要執行的命令字符串。
            env (dict): 環境變量字典。
        """
        try:
            import subprocess
            self.process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_path,
                env={**os.environ, **env},
                # Windows 特定：創建新的進程組以便於一併終止子進程
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            self.is_running = True
            # 啟動日誌讀取和資源監控任務
            asyncio.create_task(self.read_logs())
            asyncio.create_task(self.monitor_resources())
            logger.info(f"Started managed process for {self.name} (PID: {self.process.pid})")
        except Exception as e:
            logger.error(f"Failed to start process for {self.name}: {e}")

    async def monitor_resources(self):
        """
        定期監控進程及其子進程的資源使用情況 (CPU, RAM)。
        每 3 秒更新一次並廣播給客戶端。
        """
        try:
            # 注意: 如果 start 失敗，self.process.pid 可能為 None，但 start() 會處理異常。
            if not self.process:
                return

            p = psutil.Process(self.process.pid)
            while self.is_running:
                try:
                    cpu_percent = 0.0
                    memory_bytes = 0.0
                    
                    # 獲取所有子進程以計算總資源消耗
                    children = p.children(recursive=True)
                    for child in [p] + children:
                        try:
                            # interval=None 表示非阻塞，使用自上次調用以來的時間計算
                            cpu_percent += child.cpu_percent(interval=None)
                            memory_bytes += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                            
                    self.stats = {
                        "cpu": round(cpu_percent, 1),
                        "ram": round(memory_bytes / (1024 * 1024), 1) # MB
                    }
                    
                    # [v12.0] 閾值警報系統
                    new_alert = "normal"
                    if self.stats["cpu"] > 80 or self.stats["ram"] > 1024:
                        new_alert = "warning"
                    if self.stats["cpu"] > 95 or self.stats["ram"] > 2048:
                        new_alert = "critical"
                    
                    self.alert_level = new_alert

                    # 更新歷史記錄
                    self.cpu_history.append(self.stats["cpu"])
                    self.ram_history.append(self.stats["ram"])
                    
                    # [v12.0] 持久化存儲
                    if self.db_manager:
                        self.db_manager.store_metric(self.project_path, self.stats["cpu"], self.stats["ram"])

                    await self.connection_manager.broadcast({
                        "type": "process_stats",
                        "path": self.project_path,
                        "stats": self.stats,
                        "alert_level": self.alert_level,
                        "history": {
                            "cpu": list(self.cpu_history),
                            "ram": list(self.ram_history)
                        }
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Resource monitoring failed for {self.name}: {e}")

    async def read_logs(self):
        """
        持續讀取進程的 stdout，檢測錯誤關鍵字並廣播日誌內容。
        """
        if not self.process or not self.process.stdout:
            return

        logger.info(f"Log reader started for {self.name} (PID: {self.process.pid})")
        error_keywords = ['error', 'failed', 'exception', 'critical', 'err:', 'fatal']
        
        while self.is_running:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    logger.info(f"Log stream reached EOF for {self.name}")
                    break
                
                text = line.decode('utf-8', errors='ignore').rstrip()
                if text:
                    # [v10.4] 錯誤檢測
                    lower_text = text.lower()
                    if any(kw in lower_text for kw in error_keywords):
                        if not self.has_error:
                            self.has_error = True
                            await self.connection_manager.broadcast({
                                "type": "process_error",
                                "path": self.project_path,
                                "has_error": True
                            })

                    logger.info(f"[{self.name}] {text}")
                    
                    # [v12.0] 持久化存儲日誌
                    if self.db_manager:
                        self.db_manager.store_log(self.project_path, text)

                    await self.connection_manager.broadcast({
                        "type": "log",
                        "project": self.name,
                        "path": self.project_path,
                        "content": text
                    })
            except Exception as e:
                logger.error(f"Error reading logs for {self.name}: {e}")
                break
        
        self.is_running = False
        await self.connection_manager.broadcast({
            "type": "log_status",
            "project": self.name,
            "path": self.project_path,
            "status": "stopped"
        })

    def stop(self):
        """
        停止進程及其所有子進程。
        """
        if self.process:
            pid = self.process.pid
            try:
                # [v13.?) Force Kill for Windows to prevent Zombies
                if os.name == 'nt':
                     import subprocess
                     subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Unix-like cleanup
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            except Exception as e:
                logger.error(f"Stop process {self.name} failed: {e}")
            self.is_running = False
