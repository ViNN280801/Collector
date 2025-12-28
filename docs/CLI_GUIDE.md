# РУКОВОДСТВО ПО CLI ИНТЕРФЕЙСУ

**Версия документа:** 1.0
**Дата:** 2025-12-20

---

## СОДЕРЖАНИЕ

1. [Введение](#1-введение)
2. [Быстрый старт](#2-быстрый-старт)
3. [Аргументы командной строки](#3-аргументы-командной-строки)
4. [Примеры использования](#4-примеры-использования)
5. [Обработка ошибок](#5-обработка-ошибок)
6. [Интеграция в скрипты](#6-интеграция-в-скрипты)

---

## 1. ВВЕДЕНИЕ

### 1.1. Назначение документа

Настоящий документ описывает CLI (Command Line Interface) интерфейс системы Collector, включая все доступные аргументы командной строки, примеры использования и обработку ошибок.

### 1.2. Команда запуска

После установки пакета доступна команда:

```bash
log-collector-cli
```

Или через Python модуль:

```bash
python -m src.cli.main
```

### 1.3. Справка

Для получения справки по всем доступным аргументам:

```bash
log-collector-cli --help
```

---

## 2. БЫСТРЫЙ СТАРТ

### 2.1. Минимальный пример

**Базовое использование:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs
```

Этот пример:

- Собирает все файлы из `/var/log` (рекурсивно)
- Копирует их в `/backup/logs`
- Сохраняет структуру директорий

### 2.2. Пример с фильтрацией

**Сбор только лог-файлов:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns "*.log" \
  --pattern-type glob
```

Этот пример:

- Собирает только файлы с расширением `.log`
- Использует glob-шаблон для фильтрации

---

## 3. АРГУМЕНТЫ КОМАНДНОЙ СТРОКИ

### 3.1. Обязательные аргументы

#### 3.1.1. `--source-paths`

**Описание:** Список исходных путей (файлы или директории)

**Тип:** Список строк

**Пример:**

```bash
--source-paths /var/log /tmp /home/user/documents
```

**Особенности:**

- Можно указать несколько путей
- Поддерживаются как файлы, так и директории
- Для директорий выполняется рекурсивный обход

**Ошибки:**

**Ошибка - путь не существует:**

```bash
log-collector-cli \
  --source-paths /nonexistent/path \
  --target-path /backup/logs
```

**Вывод:**

```log
Error: Source path does not exist: /nonexistent/path
```

**Ошибка - отсутствие аргумента:**

```bash
log-collector-cli --target-path /backup/logs
```

**Вывод:**

```log
usage: log-collector-cli [-h] --source-paths SOURCE_PATHS [SOURCE_PATHS ...] ...
log-collector-cli: error: the following arguments are required: --source-paths
```

#### 3.1.2. `--target-path`

**Описание:** Целевой путь для сохранения файлов

**Тип:** Строка

**Пример:**

```bash
--target-path /backup/logs
```

**Особенности:**

- Должен быть валидным путем
- Директория будет создана автоматически, если не существует
- Сохраняется структура исходных директорий

**Ошибки:**

**Ошибка - отсутствие аргумента:**

```bash
log-collector-cli --source-paths /var/log
```

**Вывод:**

```log
usage: log-collector-cli [-h] --source-paths SOURCE_PATHS [SOURCE_PATHS ...] ...
log-collector-cli: error: the following arguments are required: --target-path
```

**Ошибка - недостаточно прав для записи:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /root/backup
```

**Вывод:**

```log
Error: Permission denied: /root/backup
```

### 3.2. Опциональные аргументы

#### 3.2.1. `--patterns`

**Описание:** Список шаблонов для фильтрации файлов

**Тип:** Список строк

**По умолчанию:** Нет (собираются все файлы)

**Пример:**

```bash
--patterns "*.log" "*.txt" "app_*.json"
```

**Особенности:**

- Можно указать несколько шаблонов
- Файл считается подходящим, если соответствует хотя бы одному шаблону
- Работает в комбинации с `--pattern-type`

**Ошибки:**

**Ошибка - неверный формат шаблона (для regex):**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns "*.log[" \
  --pattern-type regex
```

**Вывод:**

```log
Error: Invalid regex pattern: '*.log['. Error: unterminated character set at position 6
```

#### 3.2.2. `--pattern-type`

**Описание:** Тип шаблона для фильтрации

**Тип:** Строка (выбор из: `glob`, `regex`)

**По умолчанию:** `glob`

**Пример:**

```bash
--pattern-type regex
```

**Особенности:**

- `glob` - простые шаблоны (например, `*.log`, `file_*.txt`)
- `regex` - регулярные выражения (например, `.*\.log$`, `^app_.*`)

**Примеры шаблонов:**

**Glob шаблоны:**

```bash
--patterns "*.log" "*.txt" "file_*"
```

**Regex шаблоны:**

```bash
--patterns ".*\.log$" "^app_.*" ".*\d{4}-\d{2}-\d{2}.*"
```

**Ошибки:**

**Ошибка - неверный тип шаблона:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --pattern-type invalid
```

**Вывод:**

```log
usage: log-collector-cli [-h] ...
log-collector-cli: error: argument --pattern-type: invalid choice: 'invalid' (choose from 'glob', 'regex')
```

#### 3.2.3. `--operation-mode`

**Описание:** Режим операции с файлами

**Тип:** Строка (выбор из: `copy`, `move`, `move_remove`)

**По умолчанию:** `copy`

**Пример:**

```bash
--operation-mode move
```

**Режимы:**

**`copy`** - копирование файлов:

- Исходные файлы остаются на месте
- Создаются копии в целевой директории
- Безопасный режим (не удаляет исходные файлы)

**`move`** - перемещение файлов:

- Файлы перемещаются из исходной директории в целевую
- Исходные файлы удаляются после успешного копирования
- Может быть отменено при ошибке

**`move_remove`** - перемещение с гарантированным удалением:

- Файлы перемещаются и исходные удаляются
- Гарантированное удаление даже при ошибках
- Используется для освобождения места на диске

**Ошибки:**

**Ошибка - неверный режим:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --operation-mode invalid
```

**Вывод:**

```log
usage: log-collector-cli [-h] ...
log-collector-cli: error: argument --operation-mode: invalid choice: 'invalid' (choose from 'copy', 'move', 'move_remove')
```

**Ошибка - недостаточно места на диске:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --operation-mode move
```

**Вывод:**

```log
Error: Insufficient disk space. Required: 10.5 GB, Available: 1.2 GB
```

#### 3.2.4. `--create-archive`

**Описание:** Создавать ли архив после сбора файлов

**Тип:** Флаг (без значения)

**По умолчанию:** `False`

**Пример:**

```bash
--create-archive
```

**Особенности:**

- Создает архив после успешного сбора всех файлов
- Формат архива определяется аргументом `--archive-format`
- Архив создается в целевой директории

**Ошибки:**

**Ошибка - недостаточно места для архива:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive
```

**Вывод:**

```log
Error: Insufficient disk space for archive creation
```

#### 3.2.5. `--archive-format`

**Описание:** Формат архива

**Тип:** Строка (выбор из: `zip`, `tar`, `7z`)

**По умолчанию:** `zip`

**Пример:**

```bash
--archive-format tar
```

**Форматы:**

**`zip`** - ZIP архив:

- Универсальный формат
- Хорошее сжатие
- Поддержка на всех платформах

**`tar`** - TAR архив:

- Unix-ориентированный формат
- Может использоваться с сжатием (gzip, bzip2, xz)
- Сохраняет права доступа

**`7z`** - 7Z архив:

- Высокое сжатие
- Требует библиотеку py7zr
- Может быть медленнее других форматов

**Ошибки:**

**Ошибка - неверный формат:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive \
  --archive-format rar
```

**Вывод:**

```log
usage: log-collector-cli [-h] ...
log-collector-cli: error: argument --archive-format: invalid choice: 'rar' (choose from 'zip', 'tar', '7z')
```

#### 3.2.6. `--archive-compression`

**Описание:** Сжатие для TAR архивов

**Тип:** Строка (выбор из: `gzip`, `bzip2`, `xz`)

**По умолчанию:** Нет (без сжатия для TAR)

**Пример:**

```bash
--archive-compression gzip
```

**Особенности:**

- Применяется только для TAR архивов
- Игнорируется для ZIP и 7Z (они имеют встроенное сжатие)
- Влияет на скорость создания и размер архива

**Варианты сжатия:**

**`gzip`** - GZIP сжатие:

- Быстрое сжатие
- Хорошее соотношение скорость/размер
- Расширение `.tar.gz`

**`bzip2`** - BZIP2 сжатие:

- Медленнее, но лучше сжимает
- Расширение `.tar.bz2`

**`xz`** - XZ сжатие:

- Самое медленное, но лучшее сжатие
- Расширение `.tar.xz`

**Ошибки:**

**Ошибка - использование сжатия для ZIP:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive \
  --archive-format zip \
  --archive-compression gzip
```

**Вывод:**

```log
Warning: archive-compression is ignored for ZIP format (using built-in compression)
```

#### 3.2.7. `--collect-system-info` / `--no-collect-system-info`

**Описание:** Собирать ли системную информацию

**Тип:** Флаг

**По умолчанию:** `True` (собирается)

**Пример:**

```bash
--collect-system-info
```

или

```bash
--no-collect-system-info
```

**Особенности:**

- По умолчанию системная информация собирается
- Сохраняется в файл `pc_info.json` в целевой директории
- Включает информацию о CPU, памяти, дисках, процессах

**Ошибки:**

**Ошибка - недостаточно прав для сбора системной информации:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --collect-system-info
```

**Вывод:**

```log
Warning: Failed to collect system information: Permission denied
```

#### 3.2.8. `--locale`

**Описание:** Язык интерфейса

**Тип:** Строка (выбор из: `ru`, `en`)

**По умолчанию:** Автоопределение

**Пример:**

```bash
--locale ru
```

**Особенности:**

- Определяется автоматически из системных настроек
- Можно переопределить вручную
- Влияет на сообщения об ошибках и вывод

---

## 4. ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### 4.1. Базовые примеры

#### 4.1.1. Простое копирование

**Задача:** Скопировать все файлы из директории

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs
```

**Вывод:**

```log
Progress: 100.0% (1000/1000) - Current file: /var/log/app.log
============================================================================================
Collection Results
============================================================================================
Total files: 1000
Processed files: 1000
Failed files: 0
Target path: /backup/logs
============================================================================================
```

#### 4.1.2. Фильтрация по шаблону

**Задача:** Собрать только лог-файлы

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns "*.log" \
  --pattern-type glob
```

**Вывод:**

```log
Progress: 100.0% (500/500) - Current file: /var/log/app.log
============================================================================================
Collection Results
============================================================================================
Total files: 500
Processed files: 500
Failed files: 0
Target path: /backup/logs
============================================================================================
```

#### 4.1.3. Использование регулярных выражений

**Задача:** Собрать файлы по регулярному выражению

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns ".*\\.log$" "^app_.*" \
  --pattern-type regex
```

**Вывод:**

```log
Progress: 100.0% (300/300) - Current file: /var/log/app_2024.log
============================================================================================
Collection Results
============================================================================================
Total files: 300
Processed files: 300
Failed files: 0
Target path: /backup/logs
============================================================================================
```

### 4.2. Продвинутые примеры

#### 4.2.1. Перемещение файлов

**Задача:** Переместить файлы (освободить место)

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --operation-mode move
```

**Вывод:**

```log
Progress: 100.0% (1000/1000) - Current file: /var/log/app.log
============================================================================================
Collection Results
============================================================================================
Total files: 1000
Processed files: 1000
Failed files: 0
Target path: /backup/logs
============================================================================================
```

**Важно:** Исходные файлы будут удалены после успешного копирования.

#### 4.2.2. Создание архива

**Задача:** Собрать файлы и создать ZIP архив

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive \
  --archive-format zip
```

**Вывод:**

```log
Progress: 100.0% (1000/1000) - Current file: /var/log/app.log
Creating archive...
Archive created: /backup/logs/archive.zip
============================================================================================
Collection Results
============================================================================================
Total files: 1000
Processed files: 1000
Failed files: 0
Target path: /backup/logs
Archive created: true
Archive path: /backup/logs/archive.zip
============================================================================================
```

#### 4.2.3. Создание TAR архива со сжатием

**Задача:** Создать TAR архив с GZIP сжатием

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --create-archive \
  --archive-format tar \
  --archive-compression gzip
```

**Вывод:**

```log
Progress: 100.0% (1000/1000) - Current file: /var/log/app.log
Creating archive...
Archive created: /backup/logs/archive.tar.gz
============================================================================================
Collection Results
============================================================================================
Total files: 1000
Processed files: 1000
Failed files: 0
Target path: /backup/logs
Archive created: true
Archive path: /backup/logs/archive.tar.gz
============================================================================================
```

#### 4.2.4. Множественные исходные пути

**Задача:** Собрать файлы из нескольких директорий

```bash
log-collector-cli \
  --source-paths /var/log /tmp /home/user/documents \
  --target-path /backup/all \
  --patterns "*.log" "*.txt"
```

**Вывод:**

```log
Progress: 100.0% (1500/1500) - Current file: /home/user/documents/file.txt
============================================================================================
Collection Results
============================================================================================
Total files: 1500
Processed files: 1500
Failed files: 0
Target path: /backup/all
============================================================================================
```

#### 4.2.5. Без сбора системной информации

**Задача:** Собрать файлы без системной информации

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --no-collect-system-info
```

**Вывод:**

```log
Progress: 100.0% (1000/1000) - Current file: /var/log/app.log
============================================================================================
Collection Results
============================================================================================
Total files: 1000
Processed files: 1000
Failed files: 0
Target path: /backup/logs
============================================================================================
```

### 4.3. Примеры с ошибками

#### 4.3.1. Несуществующий исходный путь

**Запрос:**

```bash
log-collector-cli \
  --source-paths /nonexistent/path \
  --target-path /backup/logs
```

**Вывод:**

```log
Error: Source path does not exist: /nonexistent/path
```

**Код возврата:** `1`

#### 4.3.2. Недостаточно прав

**Запрос:**

```bash
log-collector-cli \
  --source-paths /root/secret \
  --target-path /backup/logs
```

**Вывод:**

```log
Error: Permission denied: /root/secret
```

**Код возврата:** `1`

#### 4.3.3. Неверный шаблон regex

**Запрос:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs \
  --patterns "*.log[" \
  --pattern-type regex
```

**Вывод:**

```log
Error: Invalid regex pattern: '*.log['. Error: unterminated character set at position 6
```

**Код возврата:** `1`

#### 4.3.4. Недостаточно места на диске

**Запрос:**

```bash
log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs
```

**Вывод:**

```log
Error: Insufficient disk space. Required: 10.5 GB, Available: 1.2 GB
```

**Код возврата:** `1`

---

## 5. ОБРАБОТКА ОШИБОК

### 5.1. Коды возврата

| Код | Описание            |
| --- | ------------------- |
| 0   | Успешное выполнение |
| 1   | Ошибка выполнения   |

### 5.2. Типы ошибок

#### 5.2.1. Ошибки валидации

**Причина:** Неверные параметры командной строки

**Пример:**

```log
Error: Source path does not exist: /nonexistent/path
```

**Решение:** Проверить корректность путей и параметров

#### 5.2.2. Ошибки доступа

**Причина:** Недостаточно прав для доступа к файлам или директориям

**Пример:**

```log
Error: Permission denied: /root/secret
```

**Решение:** Запустить с соответствующими правами или изменить пути

#### 5.2.3. Ошибки операций

**Причина:** Ошибки при выполнении операций с файлами

**Пример:**

```log
Error: Collection failed: Permission denied
```

**Решение:** Проверить права доступа и доступность файлов

#### 5.2.4. Ошибки валидации шаблонов

**Причина:** Неверный формат шаблона (особенно для regex)

**Пример:**

```log
Error: Invalid regex pattern: '*.log['. Error: unterminated character set at position 6
```

**Решение:** Проверить корректность регулярного выражения

### 5.3. Обработка в скриптах

**Пример обработки ошибок в bash:**

```bash
#!/bin/bash

if log-collector-cli \
  --source-paths /var/log \
  --target-path /backup/logs; then
  echo "Collection completed successfully"
else
  echo "Collection failed with error code: $?"
  exit 1
fi
```

**Пример обработки ошибок в Python:**

```python
import subprocess
import sys

result = subprocess.run(
    [
        "log-collector-cli",
        "--source-paths", "/var/log",
        "--target-path", "/backup/logs"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Collection completed successfully")
    print(result.stdout)
else:
    print("Collection failed")
    print(result.stderr)
    sys.exit(result.returncode)
```

---

## 6. ИНТЕГРАЦИЯ В СКРИПТЫ

### 6.1. Bash скрипты

**Пример автоматического бэкапа:**

```bash
#!/bin/bash

SOURCE_DIR="/var/log"
BACKUP_DIR="/backup/logs/$(date +%Y-%m-%d)"
PATTERNS=("*.log" "*.txt")

log-collector-cli \
  --source-paths "$SOURCE_DIR" \
  --target-path "$BACKUP_DIR" \
  --patterns "${PATTERNS[@]}" \
  --create-archive \
  --archive-format zip \
  --no-collect-system-info

if [ $? -eq 0 ]; then
  echo "Backup completed: $BACKUP_DIR"
else
  echo "Backup failed"
  exit 1
fi
```

### 6.2. Python скрипты

**Пример использования через subprocess:**

```python
import subprocess
import json
from pathlib import Path

def collect_files(source_paths, target_path, patterns=None):
    cmd = [
        "log-collector-cli",
        "--source-paths", *source_paths,
        "--target-path", str(target_path),
    ]

    if patterns:
        cmd.extend(["--patterns", *patterns])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout

# Использование
output = collect_files(
    source_paths=["/var/log"],
    target_path=Path("/backup/logs"),
    patterns=["*.log", "*.txt"]
)
print(output)
```

### 6.3. Cron задачи

**Пример cron задачи для ежедневного бэкапа:**

```cron
0 2 * * * /usr/local/bin/log-collector-cli --source-paths /var/log --target-path /backup/logs/$(date +\%Y-\%m-\%d) --create-archive --archive-format zip >> /var/log/backup.log 2>&1
```

**Объяснение:**

- `0 2 * * *` - выполнение в 2:00 каждый день
- `--source-paths /var/log` - исходная директория
- `--target-path /backup/logs/$(date +\%Y-\%m-\%d)` - целевая директория с датой
- `--create-archive --archive-format zip` - создание ZIP архива
- `>> /var/log/backup.log 2>&1` - перенаправление вывода в лог

---

## 7. ЗАКЛЮЧЕНИЕ

Настоящий документ описывает все возможности CLI интерфейса системы Collector. Для получения дополнительной информации используйте команду `log-collector-cli --help`.
