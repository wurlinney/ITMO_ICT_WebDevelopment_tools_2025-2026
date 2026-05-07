# Лабораторная работа 3: Docker, источники данных и очереди

## Цель работы

Упаковать FastAPI-приложение, базу данных и парсер данных в Docker, организовать вызов парсера через HTTP API и очередь задач Celery с Redis.

В работе использованы результаты предыдущих лабораторных:

- FastAPI-приложение и PostgreSQL-схема из лабораторной работы 1;
- логика HTML-парсера из лабораторной работы 2.

## Технологии

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Docker Compose
- Redis
- Celery
- Celery Beat
- Pydantic v2
- Uvicorn

## Общая архитектура

Приложение разделено на несколько сервисов:

| Сервис | Назначение |
| --- | --- |
| `api` | Основное FastAPI-приложение Time Manager. |
| `db` | PostgreSQL-база данных для основного приложения. |
| `parser` | Отдельный HTTP-сервис для парсинга HTML-страниц. |
| `redis` | Брокер сообщений и backend результатов Celery. |
| `celery_worker` | Воркер, выполняющий задачи парсинга из очереди. |
| `celery_beat` | Планировщик периодических задач Celery. |

Основной API не парсит страницы напрямую. Он либо синхронно обращается к сервису `parser`, либо ставит задачу в очередь Celery. Такой подход разделяет ответственность между сервисами и позволяет выполнять долгие операции в фоне.


## Подзадача 1. Упаковка приложения, БД и парсера в Docker

Для основного FastAPI-приложения создан `Dockerfile`. Контейнер:

1. Использует базовый образ `python:3.12-slim`.
2. Устанавливает зависимости из `requirements.txt`.
3. Копирует исходный код приложения и миграции Alembic.
4. Запускает приложение через `uvicorn`.
5. Работает от отдельного пользователя `appuser`, а не от `root`.

Для парсера создан отдельный сервис `parser_service` со своим `Dockerfile`. Он также запускается как FastAPI-приложение, но отвечает только за загрузку HTML и извлечение содержимого тега `<title>`.

### Docker Compose

В `docker-compose.yml` описаны сервисы:

- `db` на образе `postgres:16-alpine`;
- `api`, собираемый из основного `Dockerfile`;
- `parser`, собираемый из `parser_service/Dockerfile`;
- `redis`;
- `celery_worker`;
- `celery_beat`.

Для PostgreSQL, Redis и parser-сервиса настроены `healthcheck`. Основной API и Celery worker ждут готовности зависимых сервисов перед запуском.

## Подзадача 2. Вызов парсера из FastAPI

В основном FastAPI-приложении добавлен router `app/api/routers/parser.py`.

Синхронный endpoint:

```text
POST /parser/parse
```

Тело запроса:

```json
{
  "url": "https://example.com/"
}
```

Ответ:

```json
{
  "url": "https://example.com/",
  "title": "Example Domain"
}
```

Основной API вызывает parser-сервис по внутреннему адресу Docker-сети:

```text
http://parser:8000/parse
```

Для взаимодействия с parser-сервисом выделен отдельный модуль `app/services/parser_client.py`. Он инкапсулирует HTTP-запрос, обработку сетевых ошибок и проверку формата ответа. В FastAPI-router ошибки parser-сервиса преобразуются в корректные HTTP-ответы.

## Подзадача 3. Вызов парсера через очередь

Для фоновой обработки добавлены Redis и Celery.

В `app/worker.py` настроено Celery-приложение:

- broker: `redis://redis:6379/0`;
- result backend: `redis://redis:6379/1`;
- сериализация задач и результатов: JSON;
- отслеживание состояния задач: `task_track_started=True`.

Асинхронный endpoint:

```text
POST /parser/parse/async
```

Он принимает URL и ставит задачу `parse_url` в очередь. Клиент сразу получает идентификатор задачи:

```json
{
  "task_id": "222576ac-c73f-497f-9274-79a13a09b1f3",
  "status": "PENDING"
}
```

Для проверки результата добавлен endpoint:

```text
GET /parser/parse/async/{task_id}
```

Пример успешного ответа:

```json
{
  "task_id": "222576ac-c73f-497f-9274-79a13a09b1f3",
  "status": "SUCCESS",
  "result": {
    "url": "https://example.com/",
    "title": "Example Domain"
  },
  "error": null
}
```

Для задач парсинга настроены повторные попытки:

- до 3 повторов;
- экспоненциальная задержка между попытками.

Это снижает риск падения задачи при кратковременных сетевых ошибках или timeout внешнего сайта.

## Периодические задачи Celery

Для дополнительной части лабораторной работы добавлен сервис `celery_beat`.

В `app/worker.py` настроено расписание:

```python
beat_schedule={
    "parse-configured-url": {
        "task": "parse_periodic_url",
        "schedule": settings.periodic_parse_interval_seconds,
    },
}
```

Параметры периодической задачи вынесены в переменные окружения:

| Переменная | Назначение |
| --- | --- |
| `PERIODIC_PARSE_URL` | URL, который будет парситься по расписанию. |
| `PERIODIC_PARSE_INTERVAL_SECONDS` | Интервал запуска задачи в секундах. |

В текущей конфигурации задача запускается каждые 60 секунд и парсит `https://example.com/`.

Для `celery_beat` файл расписания расположен в `/tmp/celerybeat-schedule`, так как контейнеры работают от непривилегированного пользователя.

## Проверка работоспособности

После реализации были выполнены проверки:

```text
python -m compileall app parser_service
docker compose config
docker compose up -d --build
docker compose ps
```

Все контейнеры поднялись:

| Сервис | Состояние |
| --- | --- |
| `api` | Up |
| `db` | Up, healthy |
| `parser` | Up, healthy |
| `redis` | Up, healthy |
| `celery_worker` | Up |
| `celery_beat` | Up |

### Проверка health endpoints

Основное API:

```text
GET http://127.0.0.1:8000/health
```

Ответ:

```json
{"status": "ok"}
```

Parser-сервис:

```text
GET http://127.0.0.1:8001/health
```

Ответ:

```json
{"status": "ok"}
```

### Проверка синхронного парсинга

Запрос:

```text
POST http://127.0.0.1:8000/parser/parse
```

С телом:

```json
{"url": "https://example.com/"}
```

Результат:

```json
{
  "url": "https://example.com/",
  "title": "Example Domain"
}
```

### Проверка асинхронного парсинга

Задача создается через:

```text
POST http://127.0.0.1:8000/parser/parse/async
```

После получения `task_id` результат был проверен через:

```text
GET http://127.0.0.1:8000/parser/parse/async/{task_id}
```

Задача перешла в состояние `SUCCESS`, результат парсинга был возвращен клиенту.

### Проверка периодической задачи

В логах `celery_beat` видно, что планировщик отправляет задачу:

```text
Scheduler: Sending due task parse-configured-url (parse_periodic_url)
```

В логах `celery_worker` видно успешное выполнение:

```text
Task parse_periodic_url[...] succeeded ... {'url': 'https://example.com/', 'title': 'Example Domain'}
```

## Итоговый вывод

В лабораторной работе реализована контейнерная инфраструктура для FastAPI-приложения, базы данных, отдельного parser-сервиса и очереди задач. Основной API умеет вызывать parser как синхронно, так и через Celery. Redis используется как брокер и хранилище результатов задач. Также настроен `celery_beat` для регулярного запуска периодических задач.

Решение проверено через сборку Docker-образов, запуск всех сервисов, healthcheck, синхронный endpoint, асинхронный endpoint и периодическую задачу Celery.
