@echo off
python main2.py ^
  --package "Microsoft.Extensions.Logging" ^
  --repo "https://api.nuget.org/v3/index.json" ^
  --mode "online" ^
  --max-depth "1"
echo.
pause