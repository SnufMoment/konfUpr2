@echo off
cd /d "%~dp0"
python main4.py --package E --repo test-repo.json --mode test --max-depth 3
pause