@echo off
SETLOCAL EnableDelayedExpansion
cd /d "%~dp0"

echo ================================
echo  TaskMancer Service Stopper
echo ================================
echo.

REM Read ports from config.md
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md | Select-String 'Port : Frontend'"') do set TM_PORT_FRONTEND=%%a
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md | Select-String 'Port : Backend'"') do set TM_PORT_BACKEND=%%a

REM Default values
if not defined TM_PORT_FRONTEND set TM_PORT_FRONTEND=5173
if not defined TM_PORT_BACKEND set TM_PORT_BACKEND=8000

echo Target Ports:
echo   - Frontend: %TM_PORT_FRONTEND%
echo   - Backend:  %TM_PORT_BACKEND%
echo.

REM Stop processes using PowerShell
echo Stopping services...
powershell -Command "$stopped = $false; Get-NetTCPConnection -LocalPort %TM_PORT_BACKEND%,%TM_PORT_FRONTEND% -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | ForEach-Object { $pid = $_.OwningProcess; $port = $_.LocalPort; if ($pid -ne 0) { Write-Host \"  [OK] Stopped process on port $port (PID: $pid)\"; Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue; $stopped = $true } }; if (-not $stopped) { Write-Host '  [INFO] No services running' }"

echo.
echo ================================
echo  Services Stopped
echo ================================
echo.
pause
