@echo off
cd /d "%~dp0"
echo Running Python test runner...
uv run python _run_tests.py > _test_log.txt 2>&1
type _test_log.txt
pause
