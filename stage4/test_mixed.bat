@echo off
cd /d "%~dp0"
python main4.py --package X --repo test-repo.json --mode test --max-depth 4
pause