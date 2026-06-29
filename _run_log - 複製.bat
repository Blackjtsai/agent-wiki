@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

call :main > _test_log.txt 2>&1
type _test_log.txt
goto :eof

:main
echo === ATWK Run Log ===
echo Time: %DATE% %TIME%
echo.

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
    goto :eof
)
:found_psql
echo psql: %PSQL%

:: Step 1: Create database
echo.
echo [1/5] Create database %ATWK_DB_NAME%
set PGPASSWORD=%ATWK_DB_PASSWORD%
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "SELECT 1 FROM pg_database WHERE datname='%ATWK_DB_NAME%'" postgres 2>&1 | findstr "1 row" >nul
if %errorlevel% equ 0 (
    echo   DB already exists
) else (
    echo   Creating DB...
    "%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -c "CREATE DATABASE %ATWK_DB_NAME%" postgres 2>&1
    if !errorlevel! neq 0 ( echo ERROR: create DB failed & goto :eof )
    echo   DB created OK
)

:: Step 2: Migration
echo.
echo [2/5] Running migration...
"%PSQL%" -h %ATWK_DB_HOST% -p %ATWK_DB_PORT% -U %ATWK_DB_USER% -d %ATWK_DB_NAME% -f "db\migration_001_init.sql" 2>&1
echo   Migration done (table-already-exists errors are OK)

:: Step 3: uv sync
echo.
echo [3/5] uv sync...
uv sync 2>&1
if %errorlevel% neq 0 ( echo ERROR: uv sync failed & goto :eof )
echo   uv sync OK

:: Step 4: Start uvicorn
echo.
echo [4/5] Start uvicorn port 8300...
start "ATWK-Server" cmd /k "cd /d %~dp0 && uv run uvicorn api.main:app --reload --port 8300"
echo   Waiting 10s for server...
timeout /t 10 /nobreak >nul
echo   Server should be up

:: Step 5: Run e2e tests
echo.
echo [5/5] E2E tests...
echo ============================
uv run python tests\e2e_test.py 2>&1
set RES=!errorlevel!
echo ============================
if !RES! equ 0 ( echo PASSED ) else ( echo SOME FAILED )
echo Done: %DATE% %TIME%
goto :eof
