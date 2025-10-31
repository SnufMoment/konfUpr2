@echo off
echo ========================================
echo Тест 3: Фильтрация (исключить пакеты с "D")
echo ========================================
python main3.py ^
  --package A ^
  --repo test-repo.json ^
  --mode test ^
  --max-depth 3 ^
  --filter D

pause