@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   ATWK Run Now (no interactive prompts)
echo ============================================================

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: Read .env
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set _K=%%A
    if "!_K:~0,1!" neq "#" if "!_K!" neq "" set %%A=%%B
)

if not defined ATWK_DB_HOST set ATWK_DB_HOST=localhost
if not defined ATWK_DB_PORT set ATWK_DB_PORT=5432
if not defined ATWK_DB_NAME set ATWK_DB_NAME=db_atwk
if not defined ATWK_DB_USER set ATWK_DB_USER=postgres

echo DB: %ATWK_DB_HOST%:%ATWK_DB_PORT%/%ATWK_DB_NAME%  USER=%ATWK_DB_USER%
echo.

:: Find psql
set PSQL=psql
where psql >nul 2>&1
if %errorlevel% neq 0 (
    for %%V in (17 16 15 14 13) do (
        if exist "C:\Program Files\PostgreSQL\%%V\bin\psql.exe" (
            set "PSQL=C:\Program Files\PostgreSQL\%%V\bin\psql.exe"
            goto :found_psql
        )
    )
    echo ERROR: psql not found
    pause
    exit /b 1
)
:found_psql
echo [psql] %PSQL%

:: Step 1: Create database
echo.
echo [1/5] Creating database %ATWK_DB_NAME% ...
set PGPASSWORD=%ATWK_DB_PASSWORD%
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "SELECT 1 FROM pg_database WHERE datname='%ATWK_DB_NAME%'" postgres 2>nul | findstr "1 row" >nul
if %errorlevel% equ 0 (
    echo   DB already exists
) else (
    "%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "CREATE DATABASE %ATWK_DB_NAME%" postgres
    if !errorlevel! neq 0 ( echo ERROR: create DB failed & pause & exit /b 1 )
    echo   DB created OK
)

:: Step 2: Migration
echo.
echo [2/5] Running migration ...
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -d %ATWK_DB_NAME% -f "db\migration_001_init.sql"
echo   Migration done (errors=tables already exist is OK)

:: Step 3: uv sync
echo.
echo [3/5] uv sync ...
uv sync
if %errorlevel% neq 0 ( echo ERROR: uv sync failed & pause & exit /b 1 )
echo   Packages OK

:: Step 4: Start uvicorn
echo.
echo [4/5] Starting uvicorn port 8300 ...
start "ATWK-Server" cmd /k "cd /d %PROJECT_DIR% && uv run uvicorn api.main:app --reload --port 8300"
echo   Waiting 8 seconds...
timeout /t 8 /nobreak >nul

:: Step 5: E2E tests
echo.
echo [5/5] Running e2e tests...
echo ============================================================
uv run python tests\e2e_test.py
set RES=%errorlevel%

echo.
echo ============================================================
if %RES% equ 0 ( echo   PASSED - Layer 7 complete! ) else ( echo   SOME FAILED - see above )
echo ============================================================
echo.
pause
