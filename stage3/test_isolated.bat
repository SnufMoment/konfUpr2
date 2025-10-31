@echo off
echo ========================================
echo Тест 5: Пакет без зависимостей (E)
echo ========================================
python main3.py ^
  --package E ^
  --repo test-repo.json ^
  --mode test ^
  --max-depth 3

pause