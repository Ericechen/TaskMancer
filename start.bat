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
echo [1/2] Launching Backend API...
if "%TM_PORT_BACKEND%"=="" set TM_PORT_BACKEND=8000

:: v10.3: If managed (CI=true), use start /b to keep logs in current stdout
set START_BACKEND=start "TM Backend" cmd /k
if "%CI%"=="true" set START_BACKEND=start /b cmd /c

IF EXIST ".venv\Scripts\activate.bat" (
    %START_BACKEND% "title TM - Backend && call .venv\Scripts\activate && python backend/main.py --port %TM_PORT_BACKEND%"
) ELSE (
    echo [!] Virtual environment not found. Using global python...
    %START_BACKEND% "python backend/main.py --port %TM_PORT_BACKEND%"
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
