# Лабораторная работа 1: FastAPI Time Manager

## Цель работы

Реализовать серверное приложение на FastAPI для управления задачами и временем с использованием PostgreSQL, SQLAlchemy и Alembic.

## Технологии

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- Pydantic v2
- Uvicorn
- JWT (PyJWT)

## Краткая модель данных

Реализованные таблицы:

1. `users`
2. `categories`
3. `tasks`
4. `tags`
5. `task_tags` (many-to-many с дополнительными полями)
6. `time_logs`
7. `schedules`
8. `notifications`

### Связи

- One-to-many:
  - `users -> tasks`
  - `users -> categories`
  - `tasks -> time_logs`
  - `users -> schedules`
  - `users -> notifications`
- Many-to-many:
  - `tasks <-> tags` через связующую сущность `task_tags`

В `task_tags` есть дополнительные поля: `tagged_at`, `weight`.


## Структура финального проекта

```text
app/
  api/
    deps.py
    routers/
      auth.py
      users.py
      tasks.py
      categories.py
      tags.py
      schedules.py
      time_logs.py
      notifications.py
  core/
    config.py
    security.py
  db/
    base.py
    base_class.py
    session.py
  models/
    user.py
    task.py
    category.py
    tag.py
    task_tag.py
    time_log.py
    schedule.py
    notification.py
    enums.py
  schemas/
    auth.py
    user.py
    task.py
    category.py
    tag.py
    time_log.py
    schedule.py
    notification.py
    enums.py
  main.py

alembic/
  env.py
  versions/
    20260411_01_initial_schema.py

requirements.txt
.env.example
alembic.ini
lab_reports/
```

