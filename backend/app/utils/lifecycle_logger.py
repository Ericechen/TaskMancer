"""
進程生命週期追蹤器
用於追蹤 start/stop 的完整流程
"""
import logging
import sys
from pathlib import Path

# Setup specific logger for lifecycle events
logger = logging.getLogger("TaskMancer.Lifecycle")
logger.setLevel(logging.DEBUG)

# File Handler
LOG_FILE = Path(__file__).parent.parent.parent.parent / "lifecycle_debug.log"
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(name)s] %(message)s', datefmt='%H:%M:%S.%f'))
logger.addHandler(file_handler)

def log(source: str, action: str, path: str, details: str = ""):
    """記錄生命週期事件"""
    msg = f"[{source}] {action}: {path}"
    if details:
        msg += f" | {details}"
    logger.debug(msg)

def clear_log():
    """清除 log 檔案 (Truncate)"""
    with open(LOG_FILE, 'w', encoding='utf-8'):
        pass
    logger.info("=== Lifecycle Debug Log Started ===")

