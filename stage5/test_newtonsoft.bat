@echo off
cd /d "%~dp0"
python main5.py ^
  --package Newtonsoft.Json ^
  --repo https://api.nuget.org/v3/index.json ^
  --mode online ^
  --max-depth 2
pause