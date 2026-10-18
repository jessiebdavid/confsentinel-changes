@echo off
title ConfSentinel - Stop Backend [Port 8080]
setlocal enabledelayedexpansion

echo [INFO] Terminating Governance Engine on port 8080...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /R /C:":8080 .*LISTENING"') do (
    echo [INFO] Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo [OK] Backend stopped.