@echo off
REM TaskMancer 背景服務啟動器
REM 此檔案由 TaskMancer.vbs 呼叫

cd /d "d:\Dev\TaskMancer"

REM 從 config.md 讀取 port 設定
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md | Select-String 'Port : Frontend'"') do set TM_PORT_FRONTEND=%%a
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md | Select-String 'Port : Backend'"') do set TM_PORT_BACKEND=%%a

REM 如果讀取失敗，使用預設值
if not defined TM_PORT_FRONTEND set TM_PORT_FRONTEND=5173
if not defined TM_PORT_BACKEND set TM_PORT_BACKEND=8000

REM 啟動 Backend (完全隱藏)
IF EXIST ".venv\Scripts\activate.bat" (
    start "" /b cmd /c "call .venv\Scripts\activate && python backend/main.py --port %TM_PORT_BACKEND%" > nul 2>&1
) ELSE (
    start "" /b cmd /c "python backend/main.py --port %TM_PORT_BACKEND%" > nul 2>&1
)

REM 啟動 Frontend (完全隱藏)
cd /d "d:\Dev\TaskMancer\frontend"
start "" /b cmd /c "npm run dev -- --port %TM_PORT_FRONTEND%" > nul 2>&1
