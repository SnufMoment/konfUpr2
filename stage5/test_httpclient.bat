@echo off
cd /d "%~dp0"
python main5.py ^
  --package System.Net.Http ^
  --repo https://api.nuget.org/v3/index.json ^
  --mode online ^
  --max-depth 1
pause