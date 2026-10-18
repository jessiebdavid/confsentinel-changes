@echo off
title ConfSentinel - Stop UI [Port 8000]
setlocal enabledelayedexpansion

echo [INFO] Terminating Rio Dashboard on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo [INFO] Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo [OK] UI stopped.