@echo off
title ConfSentinel - Desktop Orchestrator (Source Dev)
setlocal enabledelayedexpansion

echo [1/2] Starting Governance Engine from source...
start "ConfSentinel Governance" cmd /c "%~dp0start-backend.bat"

echo [2/2] Polling for port 8080 readiness...
:WAIT_PORT
timeout /t 2 /nobreak >nul
netstat -ano | findstr /R /C:":8080 .*LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend ready.
    goto LAUNCH_UI
)
goto WAIT_PORT

:LAUNCH_UI
start "ConfSentinel UI" cmd /c "%~dp0start-ui.bat"
echo ==============================================================
echo  Services started from source code.
echo ==============================================================