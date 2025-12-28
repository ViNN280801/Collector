# COLLECTOR - УНИВЕРСАЛЬНАЯ СИСТЕМА СБОРА ФАЙЛОВ

**Версия:** 0.0.1
**Автор:** Semykin Vladislav <vladislav_semykin01@mail.ru>

---

## СОДЕРЖАНИЕ

1. [Описание](#1-описание)
2. [Цель проекта](#2-цель-проекта)
3. [Основные задачи](#3-основные-задачи)
4. [Архитектура и алгоритмы](#4-архитектура-и-алгоритмы)
5. [Быстрый старт](#5-быстрый-старт)
6. [Тестирование](#6-тестирование)
7. [Документация](#7-документация)

---

## 1. ОПИСАНИЕ

**Collector** - это универсальная система сбора и обработки файлов, поддерживающая три интерфейса взаимодействия:

- **CLI (Command Line Interface)** - командная строка для автоматизации и скриптов
- **REST API** - HTTP API для интеграции с другими системами
- **GUI (Graphical User Interface)** - графический интерфейс для интерактивной работы

Система предназначена для эффективного сбора файлов из указанных директорий с применением фильтрации по шаблонам, выполнения операций копирования или перемещения, создания архивов и сбора системной информации.

---

## 2. ЦЕЛЬ ПРОЕКТА

Основная цель проекта - предоставить универсальное, производительное и надежное решение для:

1. **Автоматизации сбора файлов** - массовый сбор файлов по заданным критериям
2. **Организации данных** - структурированное перемещение и копирование файлов
3. **Архивирования** - создание архивов в различных форматах (ZIP, TAR, 7Z)
4. **Мониторинга систем** - сбор информации о системе для диагностики
5. **Интеграции** - предоставление API для интеграции с другими системами

---

## 3. ОСНОВНЫЕ ЗАДАЧИ

Система выполняет следующие задачи:

### 3.1. Сбор файлов

- Рекурсивный обход директорий с поддержкой множественных исходных путей
- Фильтрация файлов по шаблонам (glob и regex)
- Обработка больших объемов файлов (тысячи и десятки тысяч файлов)

### 3.2. Операции с файлами

- **Копирование** - копирование файлов с сохранением структуры директорий
- **Перемещение** - перемещение файлов с удалением исходных
- **Перемещение с удалением** - перемещение с гарантированным удалением исходных файлов

### 3.3. Архивирование

- Создание архивов в форматах ZIP, TAR, 7Z
- Поддержка сжатия (gzip, bzip2, xz для TAR)
- Сохранение структуры директорий в архиве

### 3.4. Сбор системной информации

- Информация о процессоре, памяти, дисках
- Информация о сетевых интерфейсах
- Информация о запущенных процессах
- Экспорт в JSON формат

### 3.5. Мониторинг прогресса

- Отслеживание прогресса обработки в реальном времени
- WebSocket уведомления для API
- Callback-функции для интеграции

---

## 4. АРХИТЕКТУРА И АЛГОРИТМЫ

### 4.1. Архитектурные паттерны

#### 4.1.1. Strategy Pattern (Паттерн Стратегия)

**Применение:** Операции с файлами (копирование, перемещение)

**Реализация:** `FileOperationStrategy` с реализациями `CopyStrategy`, `MoveStrategy`, `MoveRemoveStrategy`

**Преимущества:**

- Легкое добавление новых стратегий операций
- Инкапсуляция алгоритмов операций
- Возможность динамической смены стратегии

#### 4.1.2. Builder Pattern (Паттерн Строитель)

**Применение:** Построение конфигурации сбора

**Реализация:** `CollectionConfigBuilder`

**Преимущества:**

- Пошаговое построение сложных объектов
- Гибкость в настройке параметров
- Валидация на этапе построения

#### 4.1.3. Observer Pattern (Паттерн Наблюдатель)

**Применение:** Отслеживание прогресса обработки

**Реализация:** `ProgressTracker` с подпиской на callback-функции

**Преимущества:**

- Разделение логики обработки и уведомлений
- Множественные подписчики на события
- Асинхронные уведомления

#### 4.1.4. Worker Pool Pattern (Паттерн Пул Рабочих)

**Применение:** Параллельная обработка файлов

**Реализация:** `WorkerPool` с динамическим количеством потоков

**Преимущества:**

- Эффективное использование ресурсов CPU
- Масштабируемость под нагрузку
- Контроль параллелизма

### 4.2. Алгоритмы и сложность

#### 4.2.1. Рекурсивный обход директорий

**Алгоритм:** Рекурсивный обход с использованием `Path.rglob()`

**Временная сложность:** O(N), где N - общее количество файлов и директорий

**Пространственная сложность:** O(D), где D - глубина дерева директорий (для стека рекурсии)

**Амортизационная сложность:** O(1) на файл (благодаря оптимизации Python pathlib)

**Реализация:**

```python
for filepath in source_path.rglob("*"):
    if filepath.is_file():
        all_files.append(filepath)
```

#### 4.2.2. Фильтрация файлов по шаблонам

**Алгоритм:** Линейный проход с кэшированием результатов

**Временная сложность:**

- Без кэша: O(N × M × P), где N - количество файлов, M - количество шаблонов, P - сложность шаблона
- С кэшем: O(N × M) в худшем случае, O(N) в среднем (при попадании в кэш)

**Пространственная сложность:** O(N × M) для кэша результатов

**Амортизационная сложность:** O(1) на файл при использовании кэша

**Реализация:**

```python
def match(self, filepath: Path, pattern_config: PatternConfig) -> bool:
    cache_key = f"{filepath}:{pattern_config.pattern}:{pattern_config.pattern_type}"
    if cache_key in self._cache:
        return self._cache[cache_key]  # O(1) - кэш попадание

    # O(P) - сложность зависит от типа шаблона
    if pattern_config.pattern_type == "regex":
        result = self._match_regex(pattern_config.pattern, filepath)
    else:
        result = self._match_glob(pattern_config.pattern, filepath)

    self._cache[cache_key] = result
    return result
```

**Типы шаблонов:**

- **Glob:** O(1) - простая проверка имени файла через `fnmatch`
- **Regex:** O(P), где P - длина строки пути (используется `re.search`)

#### 4.2.3. Параллельная обработка файлов

**Алгоритм:** Разделение файлов на батчи и распределение по потокам

**Временная сложность:** O(N / W), где N - количество файлов, W - количество потоков

**Пространственная сложность:** O(N) для хранения списка файлов

**Амортизационная сложность:** O(1) на файл при оптимальном количестве потоков

**Оптимальное количество потоков:**

```python
def _calculate_optimal_workers(self, total_files: int) -> int:
    return min(
        os.cpu_count() or 4,      # Количество ядер CPU
        max(1, total_files // 100),  # Один поток на 100 файлов
        MAX_WORKERS,               # Максимум 32 потока
    )
```

**Сложность батчинга:** O(N) для разделения на батчи

#### 4.2.4. Отслеживание прогресса (ProgressTracker)

**Алгоритм:** Thread-local счетчики с периодической синхронизацией

**Временная сложность:**

- Инкремент: O(1) - thread-local операция
- Flush: O(1) - атомарная операция обновления общего счетчика
- Callback уведомления: O(C), где C - количество callback-функций

**Пространственная сложность:** O(T), где T - количество потоков (для thread-local хранилища)

**Амортизационная сложность:** O(1) на инкремент благодаря батчингу

**Оптимизация:**

- Thread-local счетчики снижают количество операций блокировки в 333-500 раз
- Batch updates минимизируют contention
- Callbacks выполняются вне блокировки

**Детали оптимизации см. в:** `docs/OPTIMIZATION_EVOLUTION.md`

#### 4.2.5. Поиск общего базового пути

**Алгоритм:** Поиск наибольшего общего префикса путей

**Временная сложность:** O(N × L), где N - количество путей, L - средняя длина пути

**Пространственная сложность:** O(N × L) для хранения разрешенных путей

**Амортизационная сложность:** O(L) на путь

**Реализация:**

```python
def _find_common_base(filepaths: List[Path], source_paths: List[Path]) -> Path:
    # Разрешение путей: O(N × L)
    resolved_paths = [Path(p).resolve() for p in source_paths]

    # Поиск общего префикса: O(N × L)
    common_parts = None
    for filepath in filepaths[:10]:  # Ограничение для производительности
        # Поиск относительного пути: O(L)
        relative = filepath.resolve().relative_to(source_path)
        # Обновление общего префикса: O(L)
        ...
```

### 4.3. Структуры данных

#### 4.3.1. Кэш результатов фильтрации

**Структура:** `Dict[str, bool]` - словарь для хранения результатов сопоставления

**Операции:**

- Поиск: O(1) в среднем, O(N) в худшем случае (коллизии хэша)
- Вставка: O(1) в среднем, O(N) в худшем случае

**Использование:** Кэширование результатов сопоставления файлов с шаблонами для избежания повторных вычислений

#### 4.3.2. Thread-local хранилище

**Структура:** `threading.local()` - изолированное хранилище для каждого потока

**Операции:**

- Доступ: O(1)
- Изоляция: Гарантирована на уровне Python

**Использование:** Хранение счетчиков прогресса для каждого потока без синхронизации

#### 4.3.3. Пул потоков

**Структура:** `List[threading.Thread]` - список потоков-обработчиков

**Операции:**

- Создание потока: O(1)
- Запуск потока: O(1)
- Ожидание завершения: O(T), где T - время выполнения задачи

**Использование:** Управление параллельной обработкой файлов

---

## 5. БЫСТРЫЙ СТАРТ

### 5.1. Требования

- Python 3.7 или выше
- pip (менеджер пакетов Python)

### 5.2. Установка

#### 5.2.1. Клонирование репозитория

```bash
git clone <repository-url>
cd collector
```

#### 5.2.2. Создание виртуального окружения

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 5.2.3. Установка зависимостей

**Базовые зависимости (для использования):**

```bash
pip install -e .
```

**С зависимостями для разработки:**

```bash
pip install -e ".[dev]"
```

**Обновление зависимостей:**

```bash
pip install -e ".[dev]" --upgrade
```

### 5.3. Конфигурация (pyproject.toml)

Файл `pyproject.toml` содержит конфигурацию проекта:

#### 5.3.1. Основные секции

**`[project]`** - метаданные проекта:

- `name` - имя пакета
- `version` - версия
- `dependencies` - основные зависимости
- `requires-python` - минимальная версия Python

**`[project.optional-dependencies]`** - опциональные зависимости:

- `dev` - зависимости для разработки (black, flake8, mypy, pytest и др.)

**`[project.scripts]`** - точки входа:

- `log-collector-cli` - CLI интерфейс
- `log-collector-api` - API сервер
- `log-collector-gui` - GUI приложение

**`[tool.black]`** - настройки форматирования кода:

- `line-length = 120` - максимальная длина строки
- `target-version = ['py37']` - целевая версия Python

**`[tool.flake8]`** - настройки линтера:

- `max-line-length = 120` - максимальная длина строки
- `max-complexity = 20` - максимальная цикломатическая сложность

**`[tool.pytest.ini_options]`** - настройки тестирования:

- `timeout = 60` - таймаут для тестов
- `markers` - маркеры для категоризации тестов

**`[tool.mypy]`** - настройки статической проверки типов:

- `python_version = "3.8"` - версия Python для проверки
- `warn_return_any = true` - предупреждения о возврате Any

### 5.4. Использование

#### 5.4.1. CLI интерфейс

**Базовое использование:**

```bash
log-collector-cli --source-paths /path/to/source --target-path /path/to/target
```

**С фильтрацией по шаблону:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns "*.log" "*.txt" \
  --pattern-type glob
```

**С созданием архива:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive \
  --archive-format zip
```

**Подробнее см.:** `docs/CLI_GUIDE.md`

#### 5.4.2. REST API

**Запуск API сервера:**

```bash
log-collector-api
```

**Или через uvicorn:**

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Базовое использование:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "patterns": [{"pattern": "*.log", "pattern_type": "glob"}]
  }'
```

**Подробнее см.:** `docs/API_GUIDE.md`

#### 5.4.3. GUI интерфейс

**Запуск GUI:**

```bash
log-collector-gui
```

---

## 6. ТЕСТИРОВАНИЕ

### 6.1. Запуск тестов

**Все тесты:**

```bash
pytest .
```

**Конкретный файл:**

```bash
pytest tests/test_file_filter.py
```

**Конкретный тест:**

```bash
pytest tests/test_file_filter.py::test_match_regex
```

**С маркерами:**

```bash
pytest -m unit              # Только unit тесты
pytest -m "not slow"        # Исключить медленные тесты
pytest -m integration       # Только интеграционные тесты
```

**С подробным выводом:**

```bash
pytest -v                   # Verbose режим
pytest -vv                  # Очень подробный вывод
pytest -x                   # Остановка на первой ошибке
```

**С покрытием кода:**

```bash
pytest --cov=src --cov-report=html
```

**Только упавшие тесты:**

```bash
pytest --lf                 # Last failed
```

**Параллельное выполнение:**

```bash
pytest -n auto              # Требует pytest-xdist
```

### 6.2. Пример вывода тестов

```
====================================================================================== test session starts ======================================================================================
platform win32 -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
rootdir: C:\Users\vladislavsemykin\Downloads\collector
configfile: pyproject.toml
plugins: anyio-4.5.2, cov-5.0.0
collected 218 items

tests\test_api.py ...........                                                                                                                                                              [  5%]
tests\test_archiver.py .............                                                                                                                                                       [ 11%]
tests\test_cli.py .............                                                                                                                                                            [ 16%]
tests\test_collection_service.py ..............                                                                                                                                            [ 23%]
tests\test_exception_wrapper.py .........                                                                                                                                                  [ 27%]
tests\test_file_filter.py ..............................                                                                                                                                   [ 41%]
tests\test_file_operations.py ...............                                                                                                                                              [ 48%]
tests\test_path_sanitizer.py .........................                                                                                                                                     [ 59%]
tests\test_production_logs.py ...............                                                                                                                                              [ 66%]
tests\test_progress_tracker.py .............                                                                                                                                               [ 72%]
tests\test_security.py ...................                                                                                                                                                 [ 81%]
tests\test_validator.py ......................                                                                                                                                             [ 91%]
tests\test_worker_pool.py ...................                                                                                                                                              [100%]

======================================================================================= warnings summary ========================================================================================
venv38\lib\site-packages\_pytest\config\__init__.py:1441
  c:\users\vladislavsemykin\downloads\collector\venv38\lib\site-packages\_pytest\config\__init__.py:1441: PytestConfigWarning: Unknown config option: timeout

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
===================================================================================== slowest 10 durations ======================================================================================
3.66s call     tests/test_production_logs.py::TestProductionLogsArchiving::test_archive_production_logs_tar_gz
2.82s call     tests/test_api.py::TestAPIRateLimiting::test_rate_limiting
2.16s call     tests/test_production_logs.py::TestProductionLogsFullWorkflow::test_full_workflow_with_system_info
1.66s call     tests/test_collection_service.py::TestCollectionServicePCInfoCollector::test_collect_with_system_info
1.59s call     tests/test_production_logs.py::TestProductionLogsFullWorkflow::test_full_workflow_collect_and_archive
1.18s call     tests/test_production_logs.py::TestProductionLogsArchiving::test_archive_production_logs_with_progress
1.13s call     tests/test_production_logs.py::TestProductionLogsCollection::test_collect_production_logs_copy_mode
1.12s call     tests/test_production_logs.py::TestProductionLogsArchiving::test_archive_production_logs_zip
1.11s call     tests/test_security.py::TestRateLimiting::test_rate_limiting_resets_after_window
0.73s call     tests/test_production_logs.py::TestProductionLogsCollection::test_collect_production_logs_move_mode
================================================================================ 218 passed, 1 warning in 29.29s ================================================================================
```

**Интерпретация результатов:**

- **218 passed** - все тесты прошли успешно
- **1 warning** - одно предупреждение (неизвестная опция конфигурации)
- **29.29s** - общее время выполнения
- **slowest 10 durations** - список самых медленных тестов

### 6.3. Категории тестов

**Unit тесты** - тестирование отдельных компонентов:

- `test_file_filter.py` - фильтрация файлов
- `test_progress_tracker.py` - отслеживание прогресса
- `test_validator.py` - валидация конфигурации

**Integration тесты** - тестирование взаимодействия компонентов:

- `test_collection_service.py` - сервис сбора
- `test_worker_pool.py` - пул потоков
- `test_api.py` - API эндпоинты

**Security тесты** - тестирование безопасности:

- `test_security.py` - проверка безопасности путей, rate limiting

---

## 7. ДОКУМЕНТАЦИЯ

Подробная документация находится в директории `docs/`:

- **`docs/OPTIMIZATION_EVOLUTION.md`** - эволюция оптимизаций системы отслеживания прогресса
- **`docs/API_GUIDE.md`** - подробное руководство по REST API
- **`docs/CLI_GUIDE.md`** - подробное руководство по CLI интерфейсу

---

## 8. ТЕХНОЛОГИЧЕСКИЙ СТЕК

- **Python 3.7+** - основной язык программирования
- **FastAPI** - веб-фреймворк для REST API
- **Uvicorn** - ASGI сервер
- **Pydantic** - валидация данных
- **PyJWT** - JWT аутентификация
- **PyYAML** - работа с YAML конфигурациями
- **psutil** - сбор системной информации
- **py7zr** - поддержка формата 7Z

---

## 9. ЛИЦЕНЗИЯ

MIT License

---

**Конец документа**
