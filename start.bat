@echo off
TITLE TaskMancer Orchestrator
SETLOCAL EnableDelayedExpansion

:: 進入專案根目錄 (以防路徑不正確)
cd /d "%~dp0"

echo.
echo  [95mTaskMancer[0m - Project Intelligence
echo  -----------------------------------
echo.

:: 檢查並啟動後端 (使用新視窗)
echo  [1/2] 正在新視窗啟動後端 API...
IF EXIST ".venv" (
    start "TM Backend" cmd /k "title TM - Backend && echo 正在啟動後端... && .venv\Scripts\activate && python backend/main.py"
) ELSE (
    echo  [!] 找不到 .venv，嘗試使用全域 python 啟動...
    start "TM Backend" cmd /k "title TM - Backend && echo 正在啟動後端... && python backend/main.py"
)

:: 啟動前端 (在當前視窗持續執行)
echo  [2/2] 正在啟動前端開發伺服器...
echo 偵測路徑: "%~dp0frontend\package.json"
IF EXIST "%~dp0frontend\package.json" (
    echo [OK] 找到前端配置，準備切換目錄...
    cd /d "%~dp0frontend"
    echo [INFO] 目前工作目錄: %CD%
    echo [EXEC] 執行 npm run dev...
    call npm run dev
) ELSE (
    echo [!] 錯誤: 在 "%~dp0frontend" 找不到 package.json
    echo [DEBUG] 目前腳本路徑: %~dp0
    echo [DEBUG] 目錄清單 (dir):
    dir "%~dp0" /b
)

:: 如果前端停止，腳本也會跟著停止
pause
