@echo off
title ConfSentinel - Master Desktop Build Utility
setlocal enabledelayedexpansion

echo ==============================================================
echo    ConfSentinel Platform: Master Deployable Package Builder
echo ==============================================================

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%confsentinel-governance"
set "UI_DIR=%ROOT_DIR%confsentinel-ui"
set "DEPLOY_DIR=%ROOT_DIR%deploy"

if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"

:: --- 1. Compile Backend ---
echo.
echo [STEP 1/3] Building Governance Backend Deployable...
echo --------------------------------------------------------------
if not exist "%BACKEND_DIR%\build-backend.bat" (
    echo [ERROR] %BACKEND_DIR%\build-backend.bat missing!
    pause
    exit /b 1
)
call "%BACKEND_DIR%\build-backend.bat"
if %ERRORLEVEL% neq 0 (
    echo [FATAL] Governance engine compilation failed. Aborting master build.
    pause
    exit /b 1
)

:: --- 2. Package UI ---
echo.
echo [STEP 2/3] Building UI Deployable...
echo --------------------------------------------------------------
if not exist "%UI_DIR%\build-ui.bat" (
    echo [ERROR] %UI_DIR%\build-ui.bat missing!
    pause
    exit /b 1
)
call "%UI_DIR%\build-ui.bat"
if %ERRORLEVEL% neq 0 (
    echo [FATAL] UI packaging failed. Aborting master build.
    pause
    exit /b 1
)

:: --- 3. Generate Granular Runtime Scripts into deploy\ ---
echo.
echo [STEP 3/3] Generating Runtime Control Scripts in %DEPLOY_DIR%...

:: 1. deploy\run-backend.bat
(
    echo @echo off
    echo title ConfSentinel Governance Engine [Port 8080]
    echo setlocal enabledelayedexpansion
    echo echo ======================================================
    echo echo  ConfSentinel: Starting Pre-Compiled Governance Engine
    echo echo ======================================================
    echo where java ^^>nul 2^^>^^^&1
    echo if %%ERRORLEVEL%% neq 0 ^(
    echo     echo [ERROR] Java 21 runtime not found on PATH.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo cd /d "%%~dp0backend"
    echo set "SERVER_PORT=8080"
    echo set "SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/confsentinel"
    echo set "SPRING_DATASOURCE_USERNAME=postgres"
    echo set "SPRING_DATASOURCE_PASSWORD=postgres"
    echo set "CONFSENTINEL_GOVERNANCE_TOKEN=secret-governance-token-xyz"
    echo set "CONFSENTINEL_CI_TOKEN=secret-ci-token-abc"
    echo echo [INFO] Executing governance-engine.jar on port 8080...
    echo java -Dspring.config.additional-location=optional:application.yml -jar governance-engine.jar
) > "%DEPLOY_DIR%\run-backend.bat"

:: 2. deploy\stop-backend.bat
(
    echo @echo off
    echo title ConfSentinel - Stop Backend [Port 8080]
    echo setlocal enabledelayedexpansion
    echo echo [INFO] Locating and terminating Backend on port 8080...
    echo for /f "tokens=5" %%%%a in ^('netstat -aon ^^^| findstr /R /C:":8080 .*LISTENING"'^) do ^(
    echo     echo [INFO] Stopping Backend PID: %%%%a
    echo     taskkill /F /PID %%%%a ^^>nul 2^^>^^^&1
    echo ^)
    echo [OK] Backend stopped.
) > "%DEPLOY_DIR%\stop-backend.bat"

:: 3. deploy\run-ui.bat
(
    echo @echo off
    echo title ConfSentinel UI Dashboard [Port 8000]
    echo setlocal enabledelayedexpansion
    echo echo ======================================================
    echo echo  ConfSentinel: Starting Packaged Rio Dashboard UI
    echo echo ======================================================
    echo where python ^^>nul 2^^>^^^&1
    echo if %%ERRORLEVEL%% neq 0 ^(
    echo     echo [ERROR] Python 3.11+ not found on PATH.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo cd /d "%%~dp0ui"
    echo set "CONFSENTINEL_ENGINE_URL=http://localhost:8080"
    echo set "CONFSENTINEL_ENGINE_TOKEN=secret-governance-token-xyz"
    echo set "CONFSENTINEL_POLL_INTERVAL=10.0"
    echo set "CONFSENTINEL_UI_CONFIG_PATH=%%~dp0ui\.confsentinel\ui_config.json"
    echo if not exist ".venv\Scripts\activate.bat" ^(
    echo     echo [INFO] First-time setup: Initializing runtime environment...
    echo     python -m venv .venv
    echo     call .venv\Scripts\activate.bat
    echo     python -m pip install --upgrade pip --quiet
    echo     pip install -r requirements.txt --quiet
    echo ^) else ^(
    echo     call .venv\Scripts\activate.bat
    echo ^)
    echo echo [INFO] Launching Dashboard on http://localhost:8000...
    echo start "" "http://localhost:8000"
    echo python main.py --engine-url "%%CONFSENTINEL_ENGINE_URL%%" --token "%%CONFSENTINEL_ENGINE_TOKEN%%"
) > "%DEPLOY_DIR%\run-ui.bat"

:: 4. deploy\stop-ui.bat
(
    echo @echo off
    echo title ConfSentinel - Stop UI [Port 8000]
    echo setlocal enabledelayedexpansion
    echo echo [INFO] Locating and terminating UI Dashboard on port 8000...
    echo for /f "tokens=5" %%%%a in ^('netstat -aon ^^^| findstr /R /C:":8000 .*LISTENING"'^) do ^(
    echo     echo [INFO] Stopping UI Dashboard PID: %%%%a
    echo     taskkill /F /PID %%%%a ^^>nul 2^^>^^^&1
    echo ^)
    echo [OK] UI Dashboard stopped.
) > "%DEPLOY_DIR%\stop-ui.bat"

:: 5. deploy\run-all.bat
(
    echo @echo off
    echo title ConfSentinel - Desktop Dev Environment Runner
    echo setlocal enabledelayedexpansion
    echo echo ==============================================================
    echo echo   ConfSentinel Platform: Starting Local Dev Environment
    echo echo ==============================================================
    echo echo [1/2] Spawning Governance Backend Service...
    echo start "ConfSentinel Engine" cmd /c "%%~dp0run-backend.bat"
    echo echo [2/2] Polling for Backend Port 8080 readiness...
    echo :WAIT_PORT
    echo timeout /t 2 /nobreak ^^>nul
    echo netstat -ano ^^^| findstr /R /C:":8080 .*LISTENING" ^^>nul 2^^>^^^&1
    echo if %%ERRORLEVEL%% equ 0 ^(
    echo     echo [OK] Backend port 8080 is active.
    echo     goto START_UI
    echo ^)
    echo echo       Waiting for Backend to bind port 8080...
    echo goto WAIT_PORT
    echo :START_UI
    echo echo Starting UI Dashboard...
    echo start "ConfSentinel UI" cmd /c "%%~dp0run-ui.bat"
    echo echo ==============================================================
    echo echo  Dev Environment Online:
    echo echo   - Engine API:  http://localhost:8080
    echo echo   - Dashboard:   http://localhost:8000
    echo echo  Execute stop-all.bat to shut down all processes.
    echo echo ==============================================================
) > "%DEPLOY_DIR%\run-all.bat"

:: 6. deploy\stop-all.bat
(
    echo @echo off
    echo title ConfSentinel - Stop All Services
    echo setlocal enabledelayedexpansion
    echo echo ==============================================================
    echo echo   Stopping All ConfSentinel Services ^(Ports 8080 and 8000^)
    echo echo ==============================================================
    echo call "%%~dp0stop-backend.bat"
    echo call "%%~dp0stop-ui.bat"
    echo echo [OK] All services stopped.
    echo timeout /t 2 ^^>nul
) > "%DEPLOY_DIR%\stop-all.bat"

echo.
echo ==============================================================
echo  DEPLOYMENT BUNDLE CREATED SUCCESSFULLY!
echo.
echo  Location: %DEPLOY_DIR%
echo  Available Controls:
echo    - run-backend.bat  ^| stop-backend.bat
echo    - run-ui.bat       ^| stop-ui.bat
echo    - run-all.bat      ^| stop-all.bat
echo ==============================================================
pause
exit /b 0