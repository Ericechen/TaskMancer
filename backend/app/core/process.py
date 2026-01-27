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
        self.alert_level = "normal" # normal, warning, critical, stopping
        # [v13.17] 狀態機：確保 stop() 只執行一次
        self._stop_requested = False
        # Metrics History (v11.0) - 保留最後 300 個樣本 (~5-10 分鐘)
        self.cpu_history: Deque[float] = deque(maxlen=300)
        self.ram_history: Deque[float] = deque(maxlen=300)

    async def wait_for_port(self, port: int, timeout: float = 30.0) -> bool:
        """
        [v13.26] 等待指定 port 可連接（Health Check）。
        
        Args:
            port: 要檢查的 port
            timeout: 最大等待時間（秒）
            
        Returns:
            True 如果 port 可連接，False 如果超時
        """
        import socket
        import time
        
        start_time = time.time()
        check_interval = 0.5
        
        while time.time() - start_time < timeout:
            # 檢查是否被要求停止
            if self._stop_requested:
                return False
                
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    # Port 可連接！
                    try:
                        with open("lifecycle_debug.log", "a", encoding="utf-8") as f:
                            import datetime
                            elapsed = time.time() - start_time
                            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] HEALTH_CHECK_OK: {self.name} port {port} ready in {elapsed:.1f}s\n")
                    except: pass
                    return True
            except Exception:
                pass
                
            await asyncio.sleep(check_interval)
        
        # 超時
        try:
            with open("lifecycle_debug.log", "a", encoding="utf-8") as f:
                import datetime
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] HEALTH_CHECK_TIMEOUT: {self.name} port {port} not ready after {timeout}s\n")
        except: pass
        return False

    async def start(self, cmd: str, env: dict, health_check_port: int = None):
        """
        異步啟動子進程。

        Args:
            cmd (str): 要執行的命令字符串。
            env (dict): 環境變量字典。
            health_check_port (int): 可選，等待此 port 可連接才設置 is_running=True
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
            
            # [v13.18] 競態條件保護：如果在 start 執行期間 stop 已被調用，立即終止
            if self._stop_requested:
                logger.info(f"ABORTED START: {self.name} was stopped before start completed. Killing...")
                try:
                    with open("process_debug.log", "a", encoding="utf-8") as f:
                        import datetime
                        f.write(f"[{datetime.datetime.now()}] ABORTED START: {self.name} (PID: {self.process.pid}) - killed before start completed\n")
                except: pass
                self.process.kill()
                return
            
            # 先啟動日誌讀取（這樣可以看到啟動過程的 log）
            asyncio.create_task(self.read_logs())
            
            # [v13.26] Health Check：等待 port 可連接
            if health_check_port:
                logger.info(f"Waiting for {self.name} port {health_check_port} to be ready...")
                port_ready = await self.wait_for_port(health_check_port)
                
                if self._stop_requested:
                    return  # 被中斷
                    
                if port_ready:
                    self.is_running = True
                    self.alert_level = 'normal'
                else:
                    # 超時，但還是讓用戶可以操作
                    self.is_running = True
                    self.alert_level = 'warning'
                    logger.warning(f"{self.name} port {health_check_port} not ready after timeout, but process is running")
            else:
                # 沒有 health check port，直接設置為運行中
                self.is_running = True
            
            # 啟動資源監控
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
                    # [v13.16] Fix Flicker: Do not overwrite 'stopping' state
                    if not self._stop_requested and self.alert_level != "stopping":
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
        
        # [v13.26] 允許在 starting 狀態時繼續讀取 log（等待 health check）
        while self.is_running or self.alert_level == 'starting':
            try:
                line = await self.process.stdout.readline()
                if not line:
                    # [v13.26] 如果進程還在 starting，等一下再試
                    if self.alert_level == 'starting' and not self._stop_requested:
                        await asyncio.sleep(0.1)
                        continue
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
        
        # [v13.17] 狀態機判斷：使用 _stop_requested 區分手動停止 vs 意外退出
        # [v13.26] 額外檢查：如果還在 starting 狀態，不應該觸發 stop（health check 還沒完成）
        if not self._stop_requested and self.alert_level != 'starting':
            logger.info(f"Log stream ended unexpectedly for {self.name}. Cleaning up...")
            self.stop()
        elif self._stop_requested:
            logger.info(f"Log stream ended for {self.name} (manual stop).")
        else:
            logger.info(f"Log stream ended for {self.name} during health check - waiting.") 
        
        await self.connection_manager.broadcast({
            "type": "log_status",
            "project": self.name,
            "path": self.project_path,
            "status": "stopped"
        })

    async def wait_for_death(self, timeout=5.0):
        """
        [v13.13] Strict Lifecycle Verification
        等待進程真正從 OS 中消失。
        """
        if not self.process: return True
        
        pid = self.process.pid
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            if not psutil.pid_exists(pid):
                return True
            await asyncio.sleep(0.1)
            
        logger.warning(f"Process {pid} refused to die after {timeout}s")
        return False

    def stop(self):
        """
        停止進程及其所有子進程。
        [v13.21] 修復：允許多次調用，每次都嘗試終止進程。
        """
        # [v13.22] 詳細追蹤
        try:
            with open("lifecycle_debug.log", "a", encoding="utf-8") as f:
                import datetime
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STOP(): {self.name} | process={self.process} | pid={self.process.pid if self.process else 'None'} | is_running={self.is_running}\n")
        except: pass

        # 標記停止請求（供 start() 的 abort 邏輯使用）
        self._stop_requested = True
        self.is_running = False
        
        # 如果有進程對象，執行終止
        if self.process and self.process.pid:
            pid = self.process.pid
            try:
                # [Debug] Log Stop Attempt
                try:
                    with open("lifecycle_debug.log", "a", encoding="utf-8") as f:
                        import datetime
                        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] TASKKILL: {self.name} (PID: {pid})\n")
                except: pass

                # [v13.13] Nuclear Kill with Verification Support
                if os.name == 'nt':
                     import subprocess
                     subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Unix-like cleanup
                    try:
                        parent = psutil.Process(pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            except Exception as e:
                logger.error(f"Stop process {self.name} failed: {e}")
        else:
            # 進程還沒創建，只是標記停止狀態
            try:
                with open("lifecycle_debug.log", "a", encoding="utf-8") as f:
                    import datetime
                    f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STOP_SKIP: {self.name} - no process to kill\n")
            except: pass
            logger.info(f"Stop requested for {self.name} but process not yet created (will abort on start)")

