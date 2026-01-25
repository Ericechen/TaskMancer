@echo off
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" tray_app.py
) else (
    start "" pythonw tray_app.py
)
exit
