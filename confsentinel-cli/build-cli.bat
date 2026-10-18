```bat
@echo off
title ConfSentinel CLI - Build and Package Utility
setlocal enabledelayedexpansion

echo ==============================================================
echo       ConfSentinel CLI: Build, Package and Verify (Windows)
echo ==============================================================

:: --- 1. Python Environment Check ---
echo [1/5] Checking Python Toolchain...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [OK] Python runtime detected: %PY_VER%

:: --- 2. Clean Previous Build Artifacts & Ensure README ---
echo.
echo [2/5] Cleaning Legacy Build Artifacts...
cd /d "%~dp0"

:: Auto-create README.md if missing so hatchling does not fail
if not exist "README.md" (
    echo [INFO] README.md not found. Generating default README.md...
    (
        echo # ConfSentinel CLI
        echo Shift-Left Cloud-Native Configuration Governance CLI.
    ) > "README.md"
)

if exist "dist" (
    echo       Removing dist\ ...
    rd /s /q "dist"
)
if exist "build" (
    echo       Removing build\ ...
    rd /s /q "build"
)
for /d /r . %%d in (*.egg-info) do if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (*.dist-info) do if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"

echo [OK] Working tree cleaned.

:: --- 3. Provision Isolated Build Virtualenv ---
echo.
echo [3/5] Setting Up Isolated Build Environment...
if not exist ".venv-build\Scripts\activate.bat" (
    echo       Creating virtualenv at .venv-build...
    python -m venv .venv-build
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to initialize virtual environment.
        pause
        exit /b 1
    )
)

call .venv-build\Scripts\activate.bat
echo       Upgrading build tools (pip, build, hatchling)...
python -m pip install --upgrade pip build hatchling --quiet
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install build tooling.
    pause
    exit /b 1
)
echo [OK] Build toolchain ready.

:: --- 4. Build Wheel and Source Distribution ---
echo.
echo [4/5] Compiling and Packaging Distribution...
python -m build --outdir dist/
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Packaging failed. Check pyproject.toml syntax or missing dependencies.
    pause
    exit /b 1
)

echo.
echo Built Artifacts in .\dist:
dir /b "dist\*"

:: --- 5. Smoke Test and Self-Verification ---
echo.
echo [5/5] Performing Verification and Smoke Tests on Built Wheel...

:: Find the generated wheel file
for /f "delims=" %%f in ('dir /b /s "dist\*.whl"') do set "WHEEL_FILE=%%f"

if not defined WHEEL_FILE (
    echo [ERROR] No wheel file found in dist\ directory.
    pause
    exit /b 1
)

echo       Installing generated wheel: %WHEEL_FILE%
pip install "%WHEEL_FILE%" --force-reinstall --quiet
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install built wheel into test environment.
    pause
    exit /b 1
)

:: Verification Step A: CLI Entrypoint execution
echo       Testing 'confsentinel --help'...
confsentinel --help >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] CLI entrypoint failed to execute.
    pause
    exit /b 1
)

:: Verification Step B: Verify Wheel Resource Extraction (baseline_rules.json)
echo       Verifying embedded baseline rules package data...
python -c "import confsentinel.transport.client as c; rules = c.ResilientRuleTransportClient(None)._load_baseline(); assert len(rules) >= 3, 'Baseline rules missing!'; print(f'       [OK] Successfully loaded {len(rules)} embedded rules from wheel package.')"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Wheel package data verification failed. Resources were not bundled properly.
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo  BUILD AND PACKAGING SUCCESSFUL!
echo.
echo  Installable Wheel:
echo    %WHEEL_FILE%
echo.
echo  To install this wheel in any microservice environment, run:
echo    pip install "%WHEEL_FILE%"
echo ==============================================================
exit /b 0