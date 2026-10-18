@echo off
title ConfSentinel Governance - Build and Package Deployable
setlocal enabledelayedexpansion

echo ==============================================================
echo   ConfSentinel Governance: Build and Package Deployable Artifact
echo ==============================================================

set "MODULE_DIR=%~dp0"
set "DEPLOY_BACKEND_DIR=%MODULE_DIR%..\deploy\backend"

:: --- 1. Toolchain Verification ---
echo [1/4] Checking Java and Maven Environment...
where java >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Java runtime not found in PATH. Install JDK 21+ and set JAVA_HOME.
    pause
    exit /b 1
)

cd /d "%MODULE_DIR%"
if exist "%MODULE_DIR%mvnw.cmd" (
    set "MVN_EXEC=%MODULE_DIR%mvnw.cmd"
) else (
    where mvn >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Maven not found. Ensure mvn or mvnw.cmd is present.
        pause
        exit /b 1
    )
    set "MVN_EXEC=mvn"
)
echo [OK] Toolchain verified.

:: --- 2. Clean and Build Production JAR ---
echo.
echo [2/4] Compiling Java Sources and Packaging Executable JAR...
call %MVN_EXEC% clean package -DskipTests=false
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Maven build or test suite failed.
    pause
    exit /b 1
)

:: --- 3. Locate Packaged Artifact ---
echo.
echo [3/4] Locating Packaged Artifact...
set "BUILT_JAR="
for /f "delims=" %%i in ('dir /b /s "%MODULE_DIR%target\*.jar" 2^>nul ^| findstr /v /i "original-"') do (
    set "BUILT_JAR=%%i"
)

if not defined BUILT_JAR (
    echo [ERROR] No packaged JAR found in target\.
    pause
    exit /b 1
)
echo [OK] Found: %BUILT_JAR%

:: --- 4. Assemble Deployable Package in deploy\backend\ ---
echo.
echo [4/4] Staging Deployable Package to %DEPLOY_BACKEND_DIR%...
if exist "%DEPLOY_BACKEND_DIR%" rd /s /q "%DEPLOY_BACKEND_DIR%"
mkdir "%DEPLOY_BACKEND_DIR%" >nul 2>&1

:: Copy binary as canonical governance-engine.jar
copy /Y "%BUILT_JAR%" "%DEPLOY_BACKEND_DIR%\governance-engine.jar" >nul

:: Copy externalized configuration for runtime editing
if exist "%MODULE_DIR%src\main\resources\application.yml" (
    copy /Y "%MODULE_DIR%src\main\resources\application.yml" "%DEPLOY_BACKEND_DIR%\application.yml" >nul
)

echo.
echo ==============================================================
echo  BACKEND DEPLOYABLE PACKAGE READY!
echo  Location: %DEPLOY_BACKEND_DIR%\governance-engine.jar
echo ==============================================================
exit /b 0