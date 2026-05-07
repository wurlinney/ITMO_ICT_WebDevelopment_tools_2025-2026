# Выполнение практик 1.1–1.3

Практики выполнены и сохранены в папке `practices`.

## Практика 1.1 (`practice_1`)

В результате выполнения первой практики я реализовала базовое FastAPI-приложение, поработала с временной базой данных, реализовала CRUD по сущностям `warrior` и `profession`,, а так же добавила Pydantic-модели для валидации.

Ключевые файлы:

- `practices/practice_1/main.py`
- `practices/practice_1/models.py`

## Практика 1.2 (`practice_2`)

В ходе выполнения второй практики я перешла с временной бд на SQLModel, обновила модели `Warrior`, `Profession`, `Skill` и M2M-связь через `SkillWarriorLink`.
Так же я добавила эндпоинты для воинов, профессий, навыков и link-таблицы.

Ключевые файлы:

- `practices/practice_2/main.py`
- `practices/practice_2/models.py`
- `practices/practice_2/db.py`

## Практика 1.3 (`practice_3`)

В ходе выполнения практики 3 я настроила миграций Alembic, интегрировала переменные окружения для URL БД, и добавила поле `level` в `SkillWarriorLink`.
