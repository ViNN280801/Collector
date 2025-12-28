# РУКОВОДСТВО ПО REST API

**Версия документа:** 1.0
**Дата:** 2025-12-20

---

## СОДЕРЖАНИЕ

1. [Введение](#1-введение)
2. [Быстрый старт](#2-быстрый-старт)
3. [Аутентификация](#3-аутентификация)
4. [Эндпоинты API](#4-эндпоинты-api)
5. [WebSocket API](#5-websocket-api)
6. [Обработка ошибок](#6-обработка-ошибок)
7. [Примеры использования](#7-примеры-использования)

---

## 1. ВВЕДЕНИЕ

### 1.1. Назначение документа

Настоящий документ описывает REST API системы Collector, включая все эндпоинты, методы аутентификации, форматы запросов и ответов, а также примеры использования.

### 1.2. Базовый URL

По умолчанию API доступно по адресу:

```txt
http://localhost:8000
```

### 1.3. Версионирование

API использует версионирование через префикс пути:

```txt
/api/v1
```

Все эндпоинты доступны по пути `/api/v1/...`

### 1.4. Формат данных

API использует JSON для всех запросов и ответов. Заголовок `Content-Type: application/json` обязателен для POST запросов.

---

## 2. БЫСТРЫЙ СТАРТ

### 2.1. Запуск API сервера

**Через команду:**

```bash
log-collector-api
```

**Через uvicorn напрямую:**

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**С указанием хоста и порта:**

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8080
```

### 2.2. Проверка работоспособности

**Проверка доступности:**

```bash
curl http://localhost:8000/api/v1/collect
```

**Ожидаемый ответ (ошибка валидации - нормально):**

```json
{
  "detail": [
    {
      "loc": ["body", "source_paths"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 2.3. Документация API

После запуска сервера доступна интерактивная документация:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 3. АУТЕНТИФИКАЦИЯ

### 3.1. Обзор методов аутентификации

Система поддерживает два метода аутентификации:

1. **API Key** - простой ключ доступа через заголовок `X-API-Key`
2. **JWT (JSON Web Token)** - токен доступа через заголовок `Authorization: Bearer <token>`

Аутентификация является опциональной и настраивается при запуске сервера.

### 3.2. API Key аутентификация

#### 3.2.1. Что такое API Key

API Key - это уникальный строковый идентификатор, который используется для простой аутентификации клиентов. Каждый ключ имеет имя и может быть добавлен или удален динамически.

#### 3.2.2. Создание API Key

**Эндпоинт:** `POST /api/v1/auth/api-key`

**Запрос:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-client"
  }'
```

**Успешный ответ (200 OK):**

```json
{
  "name": "my-client",
  "api_key": "xK9mP2qR5sT8vW1yZ4aB7cD0eF3gH6iJ9kL2mN5pQ8rS1tU4vW7xY0zA3bC6dE",
  "message": "Save this API key securely. It will not be shown again."
}
```

**Ошибка - аутентификация не настроена (503 Service Unavailable):**

```json
{
  "detail": "Authentication not configured"
}
```

**Плохой пример - отсутствие имени:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-key" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 3.2.3. Использование API Key

**Запрос с API Key:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: xK9mP2qR5sT8vW1yZ4aB7cD0eF3gH6iJ9kL2mN5pQ8rS1tU4vW7xY0zA3bC6dE" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ошибка - неверный API Key (401 Unauthorized):**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ответ:**

```json
{
  "detail": "Invalid or missing API key"
}
```

**Ошибка - отсутствие API Key (если аутентификация обязательна):**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ответ:**

```json
{
  "detail": "Invalid or missing API key"
}
```

### 3.3. JWT аутентификация

#### 3.3.1. Что такое JWT

JWT (JSON Web Token) - это стандарт для безопасной передачи информации между сторонами в виде JSON объекта. Токен состоит из трех частей, разделенных точками:

1. **Header** - метаданные о токене (алгоритм, тип)
2. **Payload** - данные (user_id, exp, iat)
3. **Signature** - подпись для проверки подлинности

**Формат токена:**

```txt
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJleHAiOjE3MDAwMDAwMDB9.signature
```

#### 3.3.2. Генерация JWT токена

**Эндпоинт:** `POST /api/v1/auth/token`

**Запрос:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "expires_in": 3600
  }'
```

**Успешный ответ (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJleHAiOjE3MDAwMDAwMDB9.signature",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "admin"
}
```

**Параметры:**

- `user_id` (обязательный) - идентификатор пользователя
- `expires_in` (опциональный, по умолчанию 3600) - время жизни токена в секундах

**Плохой пример - отсутствие user_id:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_in": 3600
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "user_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Плохой пример - отрицательное время жизни:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "admin",
    "expires_in": -100
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "expires_in"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": { "limit_value": 0 }
    }
  ]
}
```

#### 3.3.3. Использование JWT токена

**Запрос с JWT токеном:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJleHAiOjE3MDAwMDAwMDB9.signature" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ошибка - неверный токен (401 Unauthorized):**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid-token" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ответ:**

```json
{
  "detail": "Invalid or expired token"
}
```

**Ошибка - истекший токен (401 Unauthorized):**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJleHAiOjE2MDAwMDAwMDB9.expired" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ответ:**

```json
{
  "detail": "Invalid or expired token"
}
```

**Ошибка - неправильный формат заголовка:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

**Ответ:**

```json
{
  "detail": "Invalid or expired token"
}
```

**Правильный формат:** `Authorization: Bearer <token>`

---

## 4. ЭНДПОИНТЫ API

### 4.1. Запуск сбора файлов

**Эндпоинт:** `POST /api/v1/collect`

**Описание:** Запускает асинхронную задачу сбора файлов. Возвращает `job_id` для отслеживания прогресса.

#### 4.1.1. Параметры запроса

**Тело запроса (JSON):**

| Параметр              | Тип                   | Обязательный | Описание                                               |
| --------------------- | --------------------- | ------------ | ------------------------------------------------------ |
| `source_paths`        | `List[str]`           | Да           | Список исходных путей (файлы или директории)           |
| `target_path`         | `str`                 | Да           | Целевой путь для сохранения файлов                     |
| `patterns`            | `List[PatternConfig]` | Нет          | Список шаблонов для фильтрации                         |
| `pattern_type`        | `str`                 | Нет          | Тип шаблона по умолчанию (`glob` или `regex`)          |
| `operation_mode`      | `str`                 | Нет          | Режим операции (`copy`, `move`, `move_remove`)         |
| `create_archive`      | `bool`                | Нет          | Создавать ли архив (по умолчанию `false`)              |
| `archive_format`      | `str`                 | Нет          | Формат архива (`zip`, `tar`, `7z`)                     |
| `archive_compression` | `str`                 | Нет          | Сжатие для TAR (`gzip`, `bzip2`, `xz`)                 |
| `collect_system_info` | `bool`                | Нет          | Собирать ли системную информацию (по умолчанию `true`) |
| `email_config`        | `EmailConfig`         | Нет          | Конфигурация для отправки email                        |

**PatternConfig:**

```json
{
  "pattern": "*.log",
  "pattern_type": "glob"
}
```

**EmailConfig:**

```json
{
  "smtp_host": "smtp.example.com",
  "smtp_port": 587,
  "username": "user@example.com",
  "password": "password",
  "from_email": "sender@example.com",
  "to_email": "recipient@example.com"
}
```

#### 4.1.2. Успешный запрос

**Пример запроса:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "patterns": [
      {"pattern": "*.log", "pattern_type": "glob"},
      {"pattern": ".*\\.txt$", "pattern_type": "regex"}
    ],
    "operation_mode": "copy",
    "create_archive": true,
    "archive_format": "zip",
    "collect_system_info": true
  }'
```

**Успешный ответ (200 OK):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started"
}
```

#### 4.1.3. Примеры ошибок

**Ошибка - отсутствие обязательных полей:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"]
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "target_path"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Ошибка - пустой список исходных путей:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": [],
    "target_path": "/backup/logs"
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "source_paths"],
      "msg": "ensure this value has at least 1 items",
      "type": "value_error.list.min_items",
      "ctx": { "limit_value": 1 }
    }
  ]
}
```

**Ошибка - неверный тип операции:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "operation_mode": "invalid_mode"
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "operation_mode"],
      "msg": "value is not a valid enumeration member; permitted: 'copy', 'move', 'move_remove'",
      "type": "type_error.enum",
      "ctx": { "enum_values": ["copy", "move", "move_remove"] }
    }
  ]
}
```

**Ошибка - неверный формат архива:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "create_archive": true,
    "archive_format": "rar"
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "archive_format"],
      "msg": "value is not a valid enumeration member; permitted: 'zip', 'tar', '7z'",
      "type": "type_error.enum",
      "ctx": { "enum_values": ["zip", "tar", "7z"] }
    }
  ]
}
```

**Ошибка - неверный тип шаблона:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "patterns": [
      {"pattern": "*.log", "pattern_type": "invalid"}
    ]
  }'
```

**Ответ (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "patterns", 0, "pattern_type"],
      "msg": "pattern_type must be 'regex' or 'glob'",
      "type": "value_error"
    }
  ]
}
```

**Ошибка - несуществующий исходный путь:**

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/nonexistent/path"],
    "target_path": "/backup/logs"
  }'
```

**Ответ (400 Bad Request):**

```json
{
  "detail": "Source path does not exist: /nonexistent/path"
}
```

### 4.2. Получение прогресса выполнения

**Эндпоинт:** `GET /api/v1/progress/{job_id}`

**Описание:** Возвращает текущий прогресс выполнения задачи.

#### 4.2.1. Параметры пути

| Параметр | Тип   | Описание             |
| -------- | ----- | -------------------- |
| `job_id` | `str` | Идентификатор задачи |

#### 4.2.2. Успешный запрос

**Пример запроса:**

```bash
curl "http://localhost:8000/api/v1/progress/550e8400-e29b-41d4-a716-446655440000"
```

**Успешный ответ (200 OK):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "percentage": 45.5,
  "current": 455,
  "total": 1000,
  "current_file": "/var/log/app.log"
}
```

#### 4.2.3. Примеры ошибок

**Ошибка - задача не найдена:**

```bash
curl "http://localhost:8000/api/v1/progress/nonexistent-job-id"
```

**Ответ (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

**Ошибка - неверный формат job_id:**

```bash
curl "http://localhost:8000/api/v1/progress/invalid-id-format"
```

**Ответ (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

### 4.3. Получение результата выполнения

**Эндпоинт:** `GET /api/v1/result/{job_id}`

**Описание:** Возвращает результат выполнения задачи. Доступен только после завершения задачи.

#### 4.3.1. Параметры пути

| Параметр | Тип   | Описание             |
| -------- | ----- | -------------------- |
| `job_id` | `str` | Идентификатор задачи |

#### 4.3.2. Успешный запрос

**Пример запроса:**

```bash
curl "http://localhost:8000/api/v1/result/550e8400-e29b-41d4-a716-446655440000"
```

**Успешный ответ (200 OK) - задача завершена:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "total_files": 1000,
    "processed_files": 1000,
    "failed_files": 0,
    "target_path": "/backup/logs",
    "archive_created": true,
    "archive_path": "/backup/logs/archive.zip",
    "pc_info_collected": true,
    "pc_info_path": "/backup/logs/pc_info.json"
  }
}
```

**Успешный ответ (200 OK) - задача завершена с ошибкой:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "results": {
    "error": "Collection failed: Permission denied"
  }
}
```

#### 4.3.3. Примеры ошибок

**Ошибка - задача не найдена:**

```bash
curl "http://localhost:8000/api/v1/result/nonexistent-job-id"
```

**Ответ (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

**Ошибка - задача еще выполняется:**

```bash
curl "http://localhost:8000/api/v1/result/550e8400-e29b-41d4-a716-446655440000"
```

**Ответ (202 Accepted):**

```json
{
  "detail": "Job is still pending. Please wait for completion."
}
```

### 4.4. Отмена задачи

**Эндпоинт:** `DELETE /api/v1/job/{job_id}`

**Описание:** Отменяет выполнение задачи и удаляет ее из репозитория.

#### 4.4.1. Параметры пути

| Параметр | Тип   | Описание             |
| -------- | ----- | -------------------- |
| `job_id` | `str` | Идентификатор задачи |

#### 4.4.2. Успешный запрос

**Пример запроса:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/job/550e8400-e29b-41d4-a716-446655440000"
```

**Успешный ответ (200 OK):**

```json
{
  "status": "cancelled"
}
```

#### 4.4.3. Примеры ошибок

**Ошибка - задача не найдена:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/job/nonexistent-job-id"
```

**Ответ (404 Not Found):**

```json
{
  "detail": "Job not found"
}
```

---

## 5. WEBSOCKET API

### 5.1. Подключение к WebSocket

**Эндпоинт:** `WS /api/v1/ws/progress/{job_id}`

**Описание:** Устанавливает WebSocket соединение для получения обновлений прогресса в реальном времени.

#### 5.1.1. Параметры пути

| Параметр | Тип   | Описание             |
| -------- | ----- | -------------------- |
| `job_id` | `str` | Идентификатор задачи |

#### 5.1.2. Подключение

**Пример подключения (JavaScript):**

```javascript
const jobId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/progress/${jobId}`);

ws.onopen = () => {
  console.log("WebSocket connected");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Progress update:", data);
  // {
  //   "job_id": "550e8400-e29b-41d4-a716-446655440000",
  //   "percentage": 45.5,
  //   "current": 455,
  //   "total": 1000,
  //   "current_file": "/var/log/app.log",
  //   "status": "pending"
  // }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket disconnected");
};
```

**Пример подключения (Python):**

```python
import asyncio
import websockets
import json

async def listen_progress(job_id: str):
    uri = f"ws://localhost:8000/api/v1/ws/progress/{job_id}"
    async with websockets.connect(uri) as websocket:
        # Получение начального состояния
        initial_data = await websocket.recv()
        print("Initial state:", json.loads(initial_data))

        # Отправка ping для поддержания соединения
        await websocket.send(json.dumps({"type": "ping"}))

        # Получение обновлений
        async for message in websocket:
            data = json.loads(message)
            print("Progress update:", data)

asyncio.run(listen_progress("550e8400-e29b-41d4-a716-446655440000"))
```

#### 5.1.3. Формат сообщений

**Сообщения от сервера:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "percentage": 45.5,
  "current": 455,
  "total": 1000,
  "current_file": "/var/log/app.log",
  "status": "pending"
}
```

**Сообщения к серверу:**

```json
{
  "type": "ping"
}
```

**Ответ на ping:**

```json
{
  "type": "pong"
}
```

#### 5.1.4. Примеры ошибок

**Ошибка - задача не найдена:**

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/api/v1/ws/progress/nonexistent-job-id"
);
ws.onerror = (error) => {
  console.error("Connection failed:", error);
};
```

**Ошибка - неверный формат job_id:**

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/api/v1/ws/progress/invalid-format"
);
ws.onerror = (error) => {
  console.error("Connection failed:", error);
};
```

---

## 6. ОБРАБОТКА ОШИБОК

### 6.1. Коды состояния HTTP

| Код | Описание             | Когда используется                                        |
| --- | -------------------- | --------------------------------------------------------- |
| 200 | OK                   | Успешный запрос                                           |
| 202 | Accepted             | Запрос принят, но обработка еще не завершена              |
| 400 | Bad Request          | Неверный формат запроса или валидация данных              |
| 401 | Unauthorized         | Ошибка аутентификации                                     |
| 404 | Not Found            | Ресурс не найден                                          |
| 422 | Unprocessable Entity | Ошибка валидации данных                                   |
| 429 | Too Many Requests    | Превышен лимит запросов (rate limiting)                   |
| 503 | Service Unavailable  | Сервис недоступен (например, аутентификация не настроена) |

### 6.2. Формат ошибок

**Стандартный формат ошибки:**

```json
{
  "detail": "Описание ошибки"
}
```

**Формат ошибки валидации:**

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Описание ошибки",
      "type": "тип_ошибки"
    }
  ]
}
```

### 6.3. Rate Limiting

API поддерживает ограничение частоты запросов (rate limiting) для защиты от злоупотреблений.

**Ошибка - превышен лимит запросов (429 Too Many Requests):**

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**Заголовки ответа:**

```txt
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700000000
```

---

## 7. ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### 7.1. Полный цикл работы с API

#### Шаг 1: Запуск сбора файлов

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs",
    "patterns": [{"pattern": "*.log", "pattern_type": "glob"}],
    "operation_mode": "copy",
    "create_archive": true,
    "archive_format": "zip"
  }'
```

**Ответ:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started"
}
```

#### Шаг 2: Отслеживание прогресса (polling)

```bash
# Получение прогресса
curl "http://localhost:8000/api/v1/progress/550e8400-e29b-41d4-a716-446655440000"
```

**Ответ:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "percentage": 75.5,
  "current": 755,
  "total": 1000,
  "current_file": "/var/log/app.log"
}
```

#### Шаг 3: Получение результата

```bash
# Проверка завершения
curl "http://localhost:8000/api/v1/result/550e8400-e29b-41d4-a716-446655440000"
```

**Ответ (если завершено):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "total_files": 1000,
    "processed_files": 1000,
    "failed_files": 0,
    "target_path": "/backup/logs",
    "archive_created": true,
    "archive_path": "/backup/logs/archive.zip"
  }
}
```

### 7.2. Использование с аутентификацией

#### Шаг 1: Создание API Key

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-client"}'
```

**Ответ:**

```json
{
  "name": "my-client",
  "api_key": "xK9mP2qR5sT8vW1yZ4aB7cD0eF3gH6iJ9kL2mN5pQ8rS1tU4vW7xY0zA3bC6dE",
  "message": "Save this API key securely. It will not be shown again."
}
```

#### Шаг 2: Использование API Key

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: xK9mP2qR5sT8vW1yZ4aB7cD0eF3gH6iJ9kL2mN5pQ8rS1tU4vW7xY0zA3bC6dE" \
  -d '{
    "source_paths": ["/var/log"],
    "target_path": "/backup/logs"
  }'
```

### 7.3. Использование WebSocket для реального времени

**JavaScript пример:**

```javascript
const jobId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/progress/${jobId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.status === "completed") {
    console.log("Task completed!");
    ws.close();
  } else {
    console.log(
      `Progress: ${data.percentage}% (${data.current}/${data.total})`
    );
  }
};
```

---

## 8. ЗАКЛЮЧЕНИЕ

Настоящий документ описывает все возможности REST API системы Collector. Для получения дополнительной информации см. интерактивную документацию по адресу `http://localhost:8000/docs` после запуска сервера.
