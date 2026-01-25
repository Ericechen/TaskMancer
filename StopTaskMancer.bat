@echo off
SETLOCAL EnableDelayedExpansion
cd /d "%~dp0"

:: 定義轉義字元以實現 ANSI 色彩
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"

echo %ESC%[95m================================%ESC%[0m
echo %ESC%[95m  TaskMancer Service Stopper    %ESC%[0m
echo %ESC%[95m================================%ESC%[0m
echo.

:: 1. 從 config.md 讀取配置
echo %ESC%[90m[1/3]%ESC%[0m 正在讀取配置...
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md -ErrorAction SilentlyContinue | Select-String 'Port : Frontend'"') do set TM_PORT_FRONTEND=%%a
for /f "tokens=5" %%a in ('powershell -Command "Get-Content config.md -ErrorAction SilentlyContinue | Select-String 'Port : Backend'"') do set TM_PORT_BACKEND=%%a

:: 預設值
if not defined TM_PORT_FRONTEND set TM_PORT_FRONTEND=5173
if not defined TM_PORT_BACKEND set TM_PORT_BACKEND=8000

echo     Frontend Port: %TM_PORT_FRONTEND%
echo     Backend Port:  %TM_PORT_BACKEND%
echo.

:: 2. 執行清理邏輯
echo %ESC%[90m[2/3]%ESC%[0m 正在終止背景服務...
powershell -Command ^
    "$ports = @(%TM_PORT_BACKEND%, %TM_PORT_FRONTEND%); ^
     $found = $false; ^
     function Kill-Tree($pid) { ^
         Get-CimInstance Win32_Process -Filter \"ParentProcessId=$pid\" | ForEach-Object { Kill-Tree $_.ProcessId }; ^
         Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue; ^
     } ^
     foreach ($port in $ports) { ^
         $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; ^
         foreach ($c in $conns) { ^
             $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; ^
             if ($p) { ^
                 Write-Host \"  %ESC%[92m[MATCH]%ESC%[0m 發現 $port 埠口進程: $($p.Name) (PID: $($p.Id))\"; ^
                 Kill-Tree $p.Id; ^
                 $found = $true; ^
             } ^
         } ^
     }; ^
     if (-not $found) { Write-Host '  %ESC%[90m[INFO]%ESC%[0m 未偵測到運行中的服務' }"

:: 3. 額外清理遺留標籤的視窗 (如果有的話)
echo.
echo %ESC%[90m[3/3]%ESC%[0m 正在進行最終清理...
powershell -Command "Get-Process | Where-Object { $_.MainWindowTitle -like '*TM - Backend*' -or $_.MainWindowTitle -like '*TM - Frontend*' } | ForEach-Object { Stop-Process -Id $_.Id -Force; Write-Host \"  %ESC%[92m[OK]%ESC%[0m 已關閉殘留視窗: $($_.MainWindowTitle)\" }"

echo.
echo %ESC%[95m================================%ESC%[0m
echo %ESC%[92m  TaskMancer 已安全停止%ESC%[0m
echo %ESC%[95m================================%ESC%[0m
echo.
timeout /t 3
