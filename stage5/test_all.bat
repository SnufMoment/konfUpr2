@echo off
cd /d "%~dp0"

call test_dag.bat
call test_cycle.bat
call test_mixed.bat
call test_filtered.bat

echo.

pause