@echo off
TITLE TaskMancer Orchestrator
SETLOCAL EnableDelayedExpansion

:: Navigate to root directory
cd /d "%~dp0"

echo.
echo   [95mTaskMancer [0m - Project Intelligence
echo  -----------------------------------
echo.

:: Step 1: Launch Backend
echo [1/2] Launching Backend API (Hidden)...
if "%TM_PORT_BACKEND%"=="" set TM_PORT_BACKEND=8000

:: Using VBS to launch backend without a window
set BACKEND_CMD=python backend/main.py --port %TM_PORT_BACKEND%
if exist ".venv\Scripts\activate.bat" (
    set BACKEND_CMD=call .venv\Scripts\activate ^&^& python backend/main.py --port %TM_PORT_BACKEND%
)

:: Create and run a temporary VBS to hide the CMD window
echo CreateObject("WScript.Shell").Run "cmd /c %BACKEND_CMD%", 0, False > %temp%\tm_backend.vbs
wscript.exe %temp%\tm_backend.vbs
del %temp%\tm_backend.vbs

:: Step 2: Launch Frontend (Current Window)
echo.
echo  [2/2] Launching Frontend Development Server...
if "%TM_PORT_FRONTEND%"=="" set TM_PORT_FRONTEND=5173
IF EXIST "frontend\package.json" (
    cd /d "%~dp0frontend"
    echo [INFO] Current Dir: %CD%
    echo [EXEC] Running npm run dev on port %TM_PORT_FRONTEND%...
    call npm run dev -- --port %TM_PORT_FRONTEND%
) ELSE (
    echo [!] ERROR: frontend\package.json not found.
    echo [DEBUG] Path tried: %~dp0frontend
)

:: Graceful exit
pause
