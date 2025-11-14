# Визуализация графа зависимостей NuGet-пакетов

## 1. Проект

Проект представляет собой консольное приложение на Python, реализующее функционал анализа зависимостей NuGet-пакетов:

- сбор графа зависимостей (с учётом транзитивности);
- определение порядка загрузки (топологическая сортировка);
- визуализация графа в формате D2 с автоматическим сохранением в SVG.

Программа полностью соответствует требованиям:

- запрещено использовать внешние менеджеры пакетов и библиотеки для анализа зависимостей;
- все данные получаются напрямую из официального NuGet API;
- поддерживается онлайн-режим (реальные пакеты) и тестовый режим (локальный JSON-репозиторий).

Режимы работы программы:

- `online` — анализ реального NuGet-пакета;
- `test` — анализ тестового репозитория с пакетами A, B, C, ...

---

## 2. Структура проекта

```
dependency-visualizer/
├── main5.py # Основной скрипт (все этапы реализации)
├── test-repo.json # Тестовый репозиторий (для режима test)
├── stage5/ # Папка с тестами этапа 5
│ ├── test_dag.bat
│ ├── test_cycle.bat
│ ├── test_mixed.bat
│ ├── test_filtered.bat
│ ├── test_logging.bat
│ └── test_all.bat
└── results/ # (автоматически создаётся при экспорте)
└── <package>_dependencies.svg # Визуализация графа зависимостей
```

---

## 3. Функции и ключевые элементы

### Основные функции

- `get_nuget_direct_deps()` — загрузка прямых зависимостей пакета через .nuspec из v3-flatcontainer.
- `dfs_build_graph()` — рекурсивное построение графа зависимостей с учётом глубины и фильтрации.
- `topological_sort()` — определение порядка установки (обработка циклов).
- `generate_d2_code()` — генерация диаграммы в формате D2.
- `export_d2_to_image()` — автоматическая визуализация и сохранение в .svg.

### Параметры запуска

| Флаг         | Описание |
|--------------|----------|
| `--package`  | Имя анализируемого пакета (обязательный). |
| `--repo`     | URL репозитория или путь к `test-repo.json` (обязательный). |
| `--mode`     | Режим работы: `online` или `test` (обязательный). |
| `--max-depth`| Максимальная глубина анализа зависимостей (обязательный, ≥0). |
| `--filter`   | Подстрока для фильтрации пакетов (опционально). |

---

## 4. Сборка и запуск

Проект не требует сборки — достаточно Python 3.8+.

### Запуск вручную

```bash
# 1. Анализ реального пакета (AutoMapper, глубина 2)
python main5.py --package AutoMapper --repo https://api.nuget.org/v3/index.json --mode online --max-depth 2

# 2. Анализ тестового пакета A
python main5.py --package A --repo test-repo.json --mode test --max-depth 3 --filter D

## Визуализация

После запуска автоматически создаётся файл:

```<package>_dependencies.svg```

Он открывается в любом браузере.

## 5. Тестирование

В папке stage5/ находятся готовые .bat-скрипты:
```
stage5/
├── test_dag.bat
├── test_cycle.bat
├── test_mixed.bat
├── test_filtered.bat
├── test_logging.bat
└── test_all.bat
```

Запуск всех тестов
```stage5\test_all.bat```

После выполнения:
выводится граф зависимостей;
показывается порядок установки;
генерируется SVG-файл.

## 6. Пример работы

### 6.1. Граф зависимостей
```
Dependency graph:
  AutoMapper -> ['Microsoft.CSharp', 'System.Reflection.Emit']
  Microsoft.CSharp -> ['NETStandard.Library', 'System.Dynamic.Runtime', ...]
  ...
```

### 6.2. Порядок загрузки

```
Installation (load) order:
  1. System.Runtime
  2. System.IO
  3. System.Reflection.Primitives
  4. System.Reflection
  ...
  13. AutoMapper
```

### 6.3. Пример D2

```
// Dependency graph in D2 format
direction: right
"AutoMapper"
"Microsoft.CSharp"
"AutoMapper" -> "Microsoft.CSharp"
"System.Reflection.Emit"
"AutoMapper" -> "System.Reflection.Emit"
...
```
![Граф зависимостей](C:\Users\Admin\Downloads\Telegram Desktop\X_dependencies.svg)


## 7. Вывод
Проект реализует:
получение зависимостей через официальное NuGet API;
построение графа с учётом глубины, фильтрации и циклов;
топологическую сортировку;
автоматическую D2→SVG визуализацию.
Программа протестирована на реальных и тестовых пакетах и соответствует требованиям задания.



