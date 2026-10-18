@echo off
title ConfSentinel - Stop All Services
setlocal enabledelayedexpansion

echo ==============================================================
echo   Stopping All ConfSentinel Services (Ports 8080 and 8000)
echo ==============================================================
call "%~dp0stop-backend.bat"
call "%~dp0stop-ui.bat"
echo [OK] All services stopped.
timeout /t 2 >nul