@echo off
cd /d "%~dp0"

echo.
echo.

call test_dag.bat
call test_cycle.bat
call test_mixed.bat
call test_filtered.bat
call test_isolated.bat

echo.
pause