import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("TaskMancer.DB")

class DatabaseManager:
    """
    資料庫管理器。
    使用 SQLite 存儲專案指標 (Metrics) 與日誌 (Logs)。
    """
    def __init__(self, db_path: str = "taskmancer.db"):
        """
        初始化 DatabaseManager。
        
        Args:
            db_path (str): SQLite 資料庫檔案路徑。
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        初始化資料庫結構。
        建立指標表、日誌表及其索引。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. 專案指標表 (CPU, RAM 趨勢)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT,
                    cpu REAL,
                    ram REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 2. 專案日誌表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 索引優化查詢效能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_path ON metrics(project_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_path ON logs(project_path)')
            conn.commit()

    def store_metric(self, project_path: str, cpu: float, ram: float):
        """
        儲存單筆資源指標。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO metrics (project_path, cpu, ram) VALUES (?, ?, ?)",
                    (project_path.lower(), cpu, ram)
                )
        except Exception as e:
            logger.error(f"DB Error (store_metric): {e}")

    def store_log(self, project_path: str, content: str):
        """
        儲存單筆專案日誌。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO logs (project_path, content) VALUES (?, ?)",
                    (project_path.lower(), content)
                )
        except Exception as e:
            logger.error(f"DB Error (store_log): {e}")

    def get_recent_metrics(self, project_path: str, limit: int = 300):
        """
        獲取專案最近的資源指標歷史記錄。
        
        Args:
            limit (int): 返回的最大筆數 (預設 300)。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT cpu, ram FROM metrics WHERE project_path = ? ORDER BY timestamp DESC LIMIT ?",
                    (project_path.lower(), limit)
                )
                rows = cursor.fetchall()
                # 轉為時間順序返回 (舊 -> 新)
                return {
                    "cpu": [r['cpu'] for r in reversed(rows)],
                    "ram": [r['ram'] for r in reversed(rows)]
                }
        except Exception as e:
            logger.error(f"DB Error (get_recent_metrics): {e}")
            return {"cpu": [], "ram": []}

    def get_recent_logs(self, project_path: str, limit: int = 500):
        """
        獲取專案最近的日誌記錄。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT content FROM logs WHERE project_path = ? ORDER BY timestamp DESC LIMIT ?",
                    (project_path.lower(), limit)
                )
                rows = cursor.fetchall()
                return [r[0] for r in reversed(rows)]
        except Exception as e:
            logger.error(f"DB Error (get_recent_logs): {e}")
            return []

    def cleanup_old_data(self, days: int = 1):
        """
        清理舊資料以防止資料庫過度膨脹。
        預設保留 1 天內的資料。
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
                conn.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff,))
                conn.execute("VACUUM")
                conn.commit()
            logger.info("Database maintenance: Old data purged.")
        except Exception as e:
            logger.error(f"DB Cleanup Error: {e}")
