@echo off
title ConfSentinel UI - Build and Package Deployable
setlocal enabledelayedexpansion

echo ==============================================================
echo   ConfSentinel UI: Test and Package Deployable Distribution
echo ==============================================================

set "MODULE_DIR=%~dp0"
set "DEPLOY_UI_DIR=%MODULE_DIR%..\deploy\ui"

:: --- 1. Python Environment Check ---
echo [1/4] Checking Python Toolchain...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH. Install Python 3.11+.
    pause
    exit /b 1
)
echo [OK] Python runtime detected.

:: --- 2. Run Test Validation in Scratch Environment ---
echo.
echo [2/4] Running UI Validation Tests...
cd /d "%MODULE_DIR%"

if exist "tests" (
    if not exist ".venv-test\Scripts\activate.bat" (
        python -m venv .venv-test
        call .venv-test\Scripts\activate.bat
        python -m pip install --upgrade pip --quiet
        pip install -r requirements.txt pytest --quiet
    ) else (
        call .venv-test\Scripts\activate.bat
    )
    python -m pytest -v tests/
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] UI automated tests failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] No tests directory found. Proceeding with packaging.
)

:: --- 3. Assemble Deployable Package in deploy\ui\ ---
echo.
echo [3/4] Staging Deployable Package to %DEPLOY_UI_DIR%...
if exist "%DEPLOY_UI_DIR%" rd /s /q "%DEPLOY_UI_DIR%"
mkdir "%DEPLOY_UI_DIR%" >nul 2>&1
mkdir "%DEPLOY_UI_DIR%\views" >nul 2>&1
mkdir "%DEPLOY_UI_DIR%\state" >nul 2>&1
mkdir "%DEPLOY_UI_DIR%\.confsentinel" >nul 2>&1

:: Copy UI application code and dependency list
copy /Y "%MODULE_DIR%main.py" "%DEPLOY_UI_DIR%\" >nul
copy /Y "%MODULE_DIR%requirements.txt" "%DEPLOY_UI_DIR%\" >nul
xcopy /E /I /Y "%MODULE_DIR%views\*" "%DEPLOY_UI_DIR%\views\" >nul
xcopy /E /I /Y "%MODULE_DIR%state\*" "%DEPLOY_UI_DIR%\state\" >nul

:: Clean temporary pycache from deploy destination
for /d /r "%DEPLOY_UI_DIR%" %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"

echo.
echo ==============================================================
echo  UI DEPLOYABLE PACKAGE READY!
echo  Location: %DEPLOY_UI_DIR%
echo ==============================================================
exit /b 0