@echo off
cd /d "%~dp0"


call test_newtonsoft.bat
call test_logging.bat
call test_httpclient.bat
call test_entityframework.bat

echo.
pause