@echo off
echo ========================================
echo Тест 1: Простой граф (пакет A, глубина 3)
echo ========================================
python main3.py ^
  --package A ^
  --repo test-repo.json ^
  --mode test ^
  --max-depth 3

pause