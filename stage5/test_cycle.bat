@echo off
cd /d "%~dp0"
python main5.py --package F --repo test-repo.json --mode test --max-depth 5
pause