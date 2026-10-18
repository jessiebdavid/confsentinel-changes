@echo off
title ConfSentinel - Policy Publisher
setlocal enabledelayedexpansion

echo ==============================================================
echo        ConfSentinel: Policy Rule Publisher
echo ==============================================================

set "ENGINE_URL=http://localhost:8080"
set "GOVERNANCE_TOKEN=cs_gov_82cd066d2038732b17129784bda2e7d74dc88b2072a9f1c76a32f7cae2c47fc8"
set "RULES_DIR=%~dp0rules"

:: 1. Verify Engine is Running
netstat -ano | findstr /R /C:":8080 .*LISTENING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Governance Engine is not running on port 8080.
    echo         Please start the backend before publishing rules.
    pause
    exit /b 1
)

:: 2. Verify Rules Directory Exists
if not exist "%RULES_DIR%" (
    echo [ERROR] Rules directory not found at "%RULES_DIR%".
    pause
    exit /b 1
)

:: 3. Export Auth Variables
set "CONFSENTINEL_ENGINE_URL=%ENGINE_URL%"
set "CONFSENTINEL_GOVERNANCE_TOKEN=%GOVERNANCE_TOKEN%"

:: 4. Execute Publisher
echo Syncing rules from: %RULES_DIR%
echo Target Engine:      %ENGINE_URL%
echo.

where confsentinel >nul 2>&1
if %ERRORLEVEL% equ 0 (
    confsentinel publish-rules --rules-dir "%RULES_DIR%" --engine-url "%ENGINE_URL%" --token "%GOVERNANCE_TOKEN%"
) else (
    python -m confsentinel.cli publish-rules --rules-dir "%RULES_DIR%" --engine-url "%ENGINE_URL%" --token "%GOVERNANCE_TOKEN%"
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Governance policies published successfully!
    echo           Inspect updated rules in dashboard: http://localhost:8000
) else (
    echo.
    echo [ERROR] Failed to publish rules. Verify token and file formats.
)

pause