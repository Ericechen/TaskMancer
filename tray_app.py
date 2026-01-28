import pystray
from PIL import Image
import subprocess
import os
import webbrowser
import threading
import sys
import time

import logging

# 設定日誌
logging.basicConfig(
    filename="tray_app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 配置
START_BAT = "start.bat"
STOP_BAT = "StopTaskMancer.bat"
ICON_PATH = "frontend/public/vite.svg" 
DASHBOARD_URL = "http://localhost:5173"

logging.info("Tray App started")

def run_bat(bat_file):
    """執行 bat 檔案且不顯示視窗"""
    args = ["cmd", "/c", bat_file]
    if bat_file == STOP_BAT:
        args.append("nopause")
    
    subprocess.Popen(args, 
                     creationflags=0x08000000, 
                     cwd=os.getcwd())

def open_dashboard():
    webbrowser.open(DASHBOARD_URL)

def on_quit(icon, item):
    run_bat(STOP_BAT)
    icon.stop()
    sys.exit(0)

def on_open(icon, item):
    open_dashboard()

def on_restart(icon, item):
    """重新啟動服務與托盤程式"""
    logging.info("Initiating restart...")
    run_bat(STOP_BAT)
    # 給一點時間讓 Stop.bat 執行
    time.sleep(2)
    icon.stop()
    
    # 重新啟動當前腳本 (使用當前的 Python 解釋器)
    python = sys.executable
    os.execl(python, python, *sys.argv)

def setup():
    try:
        logging.info(f"Setting up: running {START_BAT}")
        # 1. 啟動服務
        run_bat(START_BAT)
    except Exception as e:
        logging.error(f"Error in setup: {e}")

def create_tray():
    try:
        logging.info("Creating tray icon")
        # 優先使用生成的圖示
        icon_candidates = [
            "assets/icons/icon.ico",
            "assets/icons/app-icon.png",
            "frontend/public/vite.svg"
        ]
        
        img = None
        for path in icon_candidates:
            if os.path.exists(path):
                try:
                    logging.debug(f"Attempting to load icon from: {path}")
                    img = Image.open(path)
                    break
                except Exception as e:
                    logging.warning(f"Failed to load icon {path}: {e}")
                    continue
        
        if img is None:
            logging.info("Using default purple icon")
            img = Image.new('RGB', (64, 64), color=(124, 92, 255))

        menu = pystray.Menu(
            pystray.MenuItem("開啟儀表板", on_open, default=True),
            pystray.MenuItem("重新啟動 TaskMancer", on_restart),
            pystray.MenuItem("結束 TaskMancer", on_quit)
        )

        icon = pystray.Icon("TaskMancer", img, "TaskMancer", menu)
        
        logging.info("Running icon")
        icon.run()
    except Exception as e:
        logging.error(f"Error in create_tray: {e}")

if __name__ == "__main__":
    try:
        setup()
        create_tray()
    except Exception as e:
        logging.critical(f"Critical error in main: {e}")
