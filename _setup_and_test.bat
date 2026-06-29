@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   ATWK Setup and E2E Test
echo ============================================================
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: Step 1: .env
if not exist ".env" (
    echo [1/6] Copying .env.example to .env ...
    copy ".env.example" ".env" >nul
    echo.
    echo *** Please fill in .env in Notepad then save and close ***
    echo   ATWK_DB_USER=      (PostgreSQL user, usually postgres)
    echo   ATWK_DB_PASSWORD=  (PostgreSQL password)
    echo   ATWK_LLM_API_KEY=  (Anthropic API Key)
    echo.
    echo Press any key to open .env in Notepad...
    pause >nul
    notepad.exe ".env"
    echo Notepad closed, continuing...
) else (
    echo [1/6] .env already exists, skipping
)

:: Read .env variables
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set _LINE=%%A
    if "!_LINE:~0,1!" neq "#" (
        if "!_LINE!" neq "" (
            set %%A=%%B
        )
    )
)

if not defined ATWK_DB_HOST set ATWK_DB_HOST=localhost
if not defined ATWK_DB_PORT set ATWK_DB_PORT=5432
if not defined ATWK_DB_NAME set ATWK_DB_NAME=db_atwk
if not defined ATWK_DB_USER set ATWK_DB_USER=postgres

echo.
echo DB: %ATWK_DB_HOST%:%ATWK_DB_PORT%/%ATWK_DB_NAME%  USER: %ATWK_DB_USER%

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
    echo [ERROR] psql not found. Please add PostgreSQL to PATH.
    pause
    exit /b 1
)
:found_psql
echo [psql] %PSQL%

:: Step 2: Create database
echo.
echo [2/6] Creating database %ATWK_DB_NAME% ...
set PGPASSWORD=%ATWK_DB_PASSWORD%
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "SELECT 1 FROM pg_database WHERE datname='%ATWK_DB_NAME%'" postgres 2>nul | findstr /C:"1 row" >nul
if %errorlevel% equ 0 (
    echo   Database already exists, skipping
) else (
    "%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "CREATE DATABASE %ATWK_DB_NAME%" postgres
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create database
        pause
        exit /b 1
    )
    echo   Database created OK
)

:: Step 3: Migration
echo.
echo [3/6] Running migration_001_init.sql ...
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -d %ATWK_DB_NAME% -f "db\migration_001_init.sql"
if %errorlevel% neq 0 (
    echo [WARN] Migration had errors (tables may already exist, continuing)
)
echo   Migration done

:: Step 4: uv sync
echo.
echo [4/6] Running uv sync ...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed
    pause
    exit /b 1
)
echo   Packages installed

:: Step 5: Start uvicorn
echo.
echo [5/6] Starting uvicorn on port 8300 ...
start "ATWK Server" cmd /k "cd /d %PROJECT_DIR% && uv run uvicorn api.main:app --reload --port 8300"

echo   Waiting 8s for server to start...
timeout /t 8 /nobreak >nul

:: Step 6: E2E tests
echo.
echo [6/6] Running e2e tests...
echo ============================================================
uv run python tests\e2e_test.py
set TEST_RESULT=%errorlevel%

echo.
echo ============================================================
if %TEST_RESULT% equ 0 (
    echo   RESULT: ALL TESTS PASSED! Layer 7 complete.
) else (
    echo   RESULT: Some tests failed. Check output above.
)
echo ============================================================
echo.
pause
