import pystray
from PIL import Image
import subprocess
import os
import webbrowser
import threading
import sys
import time

# 配置
START_BAT = "start.bat"
STOP_BAT = "StopTaskMancer.bat"
ICON_PATH = "frontend/public/vite.svg" # 或者使用生成的圖示
DASHBOARD_URL = "http://localhost:5173"

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

def setup():
    # 1. 啟動服務
    run_bat(START_BAT)

def create_tray():
    # 優先使用生成的圖示
    icon_candidates = [
        "src-tauri/icons/icon.ico",
        "src-tauri/icons/32x32.png",
        "src-tauri/icons/app-icon.png",
        "frontend/public/vite.svg"
    ]
    
    img = None
    for path in icon_candidates:
        if os.path.exists(path):
            try:
                img = Image.open(path)
                break
            except:
                continue
    
    if img is None:
        img = Image.new('RGB', (64, 64), color=(124, 92, 255))

    menu = pystray.Menu(
        pystray.MenuItem("開啟儀表板", on_open, default=True),
        pystray.MenuItem("結束 TaskMancer", on_quit)
    )

    icon = pystray.Icon("TaskMancer", img, "TaskMancer", menu)
    
    # 雙擊行為 (某些系統支援，若不支援則用右鍵菜單)
    icon.run_detached()
    
    # 模擬雙擊 (pystray 本身不直接支援 double_click 事件，但 MenuItem(default=True) 會在點擊圖示時觸發)

if __name__ == "__main__":
    setup()
    create_tray()
    # 保持主線程運行
    while True:
        time.sleep(1)
