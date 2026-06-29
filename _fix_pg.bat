@echo off
cd /d "%~dp0"
uv run python _fix_pg_auth.py > _fix_pg_log.txt 2>&1
type _fix_pg_log.txt
pause
