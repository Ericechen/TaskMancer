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
IF EXIST ".venv\Scripts\activate.bat" (
    start "TM Backend" cmd /k "title TM - Backend && echo Starting Python Backend... && call .venv\Scripts\activate && python backend/main.py"
) ELSE (
    echo  [!] Virtual environment not found. Using global python...
    start "TM Backend" cmd /k "title TM - Backend && echo Starting Python Backend... && python backend/main.py"
)

:: Step 2: Launch Frontend (Current Window)
echo.
echo  [2/2] Launching Frontend Development Server...
IF EXIST "frontend\package.json" (
    cd /d "%~dp0frontend"
    echo [INFO] Current Dir: %CD%
    echo [EXEC] Running npm run dev...
    call npm run dev
) ELSE (
    echo [!] ERROR: frontend\package.json not found.
    echo [DEBUG] Path tried: %~dp0frontend
)

:: Graceful exit
pause
