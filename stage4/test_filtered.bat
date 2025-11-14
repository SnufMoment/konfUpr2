@echo off
cd /d "%~dp0"
python main4.py --package A --repo test-repo.json --mode test --max-depth 10 --filter D
pause