@echo off
set "PROJ_DIR=d:\Dev\TaskMancer"
cd /d "%PROJ_DIR%"

if exist "%PROJ_DIR%\.venv\Scripts\pythonw.exe" (
    start "" "%PROJ_DIR%\.venv\Scripts\pythonw.exe" "%PROJ_DIR%\tray_app.py"
) else (
    start "" pythonw "%PROJ_DIR%\tray_app.py"
)
exit
