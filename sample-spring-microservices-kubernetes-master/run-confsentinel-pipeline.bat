@echo off
title ConfSentinel - CI/CD Local Pipeline Runner
setlocal enabledelayedexpansion

echo ==============================================================
echo    ConfSentinel: Microservice Governance CI/CD Pipeline
echo ==============================================================

:: --- 1. Target Engine Endpoint & Security Tokens ---
set "ENGINE_URL=http://localhost:8080"
set "GOVERNANCE_TOKEN=secret-governance-token-xyz"
set "CI_TOKEN=secret-ci-token-abc"

:: Export standard environment variables (CLI picks these up automatically)
set "CONFSENTINEL_ENGINE_URL=%ENGINE_URL%"
set "CONFSENTINEL_GOVERNANCE_TOKEN=%GOVERNANCE_TOKEN%"
set "CONFSENTINEL_CI_TOKEN=%CI_TOKEN%"

:: --- 2. Target Service Metadata ---
set "SERVICE_NAME=sample-spring-microservices"
set "ENVIRONMENT=dev"
set "BRANCH=main"

:: Extract commit hash and author from git if available
where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('git rev-parse --short HEAD 2^>nul') do set "COMMIT_HASH=%%i"
    for /f "delims=" %%i in ('git log -1 --pretty^=format:%%an 2^>nul') do set "AUTHOR=%%i"
)
if not defined COMMIT_HASH set "COMMIT_HASH=local-dev-manual"
if not defined AUTHOR set "AUTHOR=%USERNAME%"

:: --- 3. Pre-Flight Check: Backend Engine Reachability ---
echo [1/3] Checking Governance Engine reachability on %ENGINE_URL%...
netstat -ano | findstr /R /C:":8080 .*LISTENING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] ConfSentinel Governance Engine is not running on port 8080!
    echo         Please start the backend first:
    echo         cd D:\Claudeworkspace\ConfSentinel ^& start-backend.bat
    pause
    exit /b 1
)
echo [OK] Backend engine is active.

:: --- 4. Toolchain Check ---
echo.
echo [2/3] Checking ConfSentinel CLI runtime...
where confsentinel >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where python >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Neither 'confsentinel' nor 'python' was found on PATH.
        pause
        exit /b 1
    )
    set "RUNNER=python -m confsentinel.cli"
) else (
    set "RUNNER=confsentinel"
)
echo [OK] Using runner: %RUNNER%

:: --- 5. Execute Scan and Telemetry Ingestion ---
:: Ensure working directory is the microservice folder
cd /d "%~dp0"

echo.
echo [3/3] Executing Governance Scan and Uploading Telemetry...
echo       Service:     %SERVICE_NAME%
echo       Environment: %ENVIRONMENT%
echo       Commit Hash: %COMMIT_HASH%
echo       Branch:      %BRANCH%
echo       Author:      %AUTHOR%
echo --------------------------------------------------------------

%RUNNER% scan ^
    --config-dir "." ^
    --engine-url "%ENGINE_URL%" ^
    --ci-token "%CI_TOKEN%" ^
    --service-name "%SERVICE_NAME%" ^
    --base-env "%ENVIRONMENT%"

set "SCAN_EXIT_CODE=%ERRORLEVEL%"

echo.
if %SCAN_EXIT_CODE% equ 0 (
    echo ==============================================================
    echo  [PASSED] Governance checks passed! No blockers detected.
    echo ==============================================================
) else (
    echo ==============================================================
    echo  [BLOCKED] Scan failed with exit code %SCAN_EXIT_CODE%.
    echo  Blocking violations found. Check dashboard: http://localhost:8000
    echo ==============================================================
)

exit /b %SCAN_EXIT_CODE%