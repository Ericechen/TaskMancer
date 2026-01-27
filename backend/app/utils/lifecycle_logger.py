"""
進程生命週期追蹤器
用於追蹤 start/stop 的完整流程
"""
import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent.parent.parent / "lifecycle_debug.log"

def log(source: str, action: str, path: str, details: str = ""):
    """記錄生命週期事件"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            f.write(f"[{timestamp}] [{source}] {action}: {path}")
            if details:
                f.write(f" | {details}")
            f.write("\n")
    except:
        pass

def clear_log():
    """清除 log 檔案"""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"=== Lifecycle Debug Log Started at {datetime.datetime.now()} ===\n")
    except:
        pass
