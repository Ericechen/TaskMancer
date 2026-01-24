@echo off
setlocal enabledelayedexpansion

:: Generate ESC character for ANSI colors in Windows Batch
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"

echo %ESC%[96m[Test Server]%ESC%[0m Starting high-fidelity ANSI simulation v10.4...
echo %ESC%[90mEnvironment: CI=%CI% (ESC sequence verified)%ESC%[0m
echo.

set /a count=1

:loop
set /a "r=!random! %% 5"

if !r! equ 0 (
    echo %ESC%[92m[%time%] SUCCESS: %ESC%[0mData packet !count! processed successfully.
) else if !r! equ 1 (
    echo %ESC%[93m[%time%] WARNING: %ESC%[0mLatency spike detected in pipe !count!.
) else if !r! equ 2 (
    echo %ESC%[91m[%time%] ERROR: %ESC%[0mFailed to sync state for entity !count!. [Critical Failure]
) else if !r! equ 3 (
    echo %ESC%[94m[%time%] INFO: %ESC%[0mInitializing subsystem !count!...
) else (
    echo %ESC%[95m[%time%] DEBUG: %ESC%[0mMemory offset 0x!random! verified.
)

set /a count+=1
timeout /t 1 >nul
goto loop
