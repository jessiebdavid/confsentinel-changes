@echo off
title ConfSentinel - Governance Engine [Port 8080]
setlocal enabledelayedexpansion

echo =======================================================
echo  ConfSentinel: Starting Central Governance Engine (Dev)
echo =======================================================

where java >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Java 21+ not found on PATH.
    pause
    exit /b 1
)

set "SERVER_PORT=8080"
set "SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/confsentinel"
set "SPRING_DATASOURCE_USERNAME=postgresadmin"
set "SPRING_DATASOURCE_PASSWORD=test@1234"
set "CONFSENTINEL_GOVERNANCE_TOKEN=cs_gov_82cd066d2038732b17129784bda2e7d74dc88b2072a9f1c76a32f7cae2c47fc8"
set "CONFSENTINEL_CI_TOKEN=secret-ci-token-abc"

:: Targets the new folder name
cd /d "%~dp0confsentinel-governance"
if not exist "pom.xml" (
    echo [ERROR] pom.xml not found in confsentinel-governance.
    pause
    exit /b 1
)

if exist "mvnw.cmd" (
    call mvnw.cmd spring-boot:run
) else (
    call mvn spring-boot:run
)