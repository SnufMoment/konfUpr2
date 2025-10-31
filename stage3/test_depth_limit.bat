@echo off
echo ========================================
echo Тест 4: Глубина = 1 (только прямые зависимости)
echo ========================================
python main3.py ^
  --package A ^
  --repo test-repo.json ^
  --mode test ^
  --max-depth 1

pause