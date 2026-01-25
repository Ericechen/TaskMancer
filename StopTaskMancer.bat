@echo off
TITLE TaskMancer Service Stopper
SETLOCAL EnableDelayedExpansion
cd /d "%~dp0"

echo ================================
echo   TaskMancer Service Stopper    
echo ================================
echo.

:: 1. Read configuration
echo [1/3] Loading environment...
if "%TM_PORT_BACKEND%"=="" set TM_PORT_BACKEND=8000
if "%TM_PORT_FRONTEND%"=="" set TM_PORT_FRONTEND=5173

echo     Backend Port:  %TM_PORT_BACKEND%
echo     Frontend Port: %TM_PORT_FRONTEND%
echo.

:: 2. Terminate Processes
echo [2/3] Stopping background services (Killing Process Tree)...

:: Fixed $pid conflict (renamed to $tPid)
powershell -Command "$ports = @(%TM_PORT_BACKEND%, %TM_PORT_FRONTEND%); $found = $false; function Kill-Tree($tPid) { try { Get-CimInstance Win32_Process -Filter \"ParentProcessId=$tPid\" -ErrorAction SilentlyContinue | ForEach-Object { Kill-Tree $_.ProcessId }; Stop-Process -Id $tPid -Force -ErrorAction SilentlyContinue; } catch {} }; foreach ($port in $ports) { $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; foreach ($c in $conns) { if ($c.OwningProcess -ne 0) { $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; if ($p) { Write-Host \"  [MATCH] Port $port Process: $($p.Name) (PID: $($p.Id))\"; Kill-Tree $p.Id; $found = $true; } } } }; $cmdProcs = Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*TM - *' -or $_.MainWindowTitle -like '*TaskMancer*' }; foreach ($cp in $cmdProcs) { Write-Host \"  [CLEANUP] Closing window: $($cp.MainWindowTitle)\"; Kill-Tree $cp.Id; $found = $true; }; if (-not $found) { Write-Host '  [INFO] No active services found.' }"

:: 3. Validation
echo.
echo [3/3] Validating status...
netstat -ano | findstr ":%TM_PORT_BACKEND% :%TM_PORT_FRONTEND%" > nul
if %errorlevel% equ 0 (
    echo   [WARNING] Some ports are still active. Please check manually.
) else (
    echo   [SUCCESS] All targeted services have been stopped.
)

echo.
echo ================================
echo     TaskMancer has Stopped      
echo ================================
echo.

:: Keep window open for review
echo Press any key to close this window...
pause
