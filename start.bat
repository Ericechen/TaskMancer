@echo off
TITLE TaskMancer Orchestrator
SETLOCAL EnableDelayedExpansion

:: Navigate to root directory
cd /d "%~dp0"

echo.
echo   [95mTaskMancer [0m - Project Intelligence
echo  -----------------------------------
echo.

:: Step 1: Launch Backend (New Window)
echo  [1/2] Launching Backend API in new window...
if "%TM_PORT_BACKEND%"=="" set TM_PORT_BACKEND=8000
IF EXIST ".venv\Scripts\activate.bat" (
    start "TM Backend" cmd /k "title TM - Backend && echo Starting Python Backend on port %TM_PORT_BACKEND%... && call .venv\Scripts\activate && python backend/main.py --port %TM_PORT_BACKEND%"
) ELSE (
    echo  [!] Virtual environment not found. Using global python...
    start "TM Backend" cmd /k "title TM - Backend && echo Starting Python Backend on port %TM_PORT_BACKEND%... && python backend/main.py --port %TM_PORT_BACKEND%"
)

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
