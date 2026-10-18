@echo off
title ConfSentinel - Rio Dashboard [Port 8000]
setlocal enabledelayedexpansion

echo =======================================================
echo  ConfSentinel: Starting Rio Dashboard UI (Dev)
echo =======================================================

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.11+ not found on PATH.
    pause
    exit /b 1
)

set "CONFSENTINEL_ENGINE_URL=http://localhost:8080"
set "CONFSENTINEL_ENGINE_TOKEN=cs_gov_82cd066d2038732b17129784bda2e7d74dc88b2072a9f1c76a32f7cae2c47fc8"
set "CONFSENTINEL_POLL_INTERVAL=10.0"
set "CONFSENTINEL_UI_CONFIG_PATH=%~dp0confsentinel-ui\.confsentinel\ui_config.json"

:: Targets the new folder name
cd /d "%~dp0confsentinel-ui"
if not exist "main.py" (
    echo [ERROR] main.py not found in confsentinel-ui.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment in .venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
) else (
    call .venv\Scripts\activate.bat
)

start "" "http://localhost:8000"
python main.py --engine-url "%CONFSENTINEL_ENGINE_URL%" --token "%CONFSENTINEL_ENGINE_TOKEN%"