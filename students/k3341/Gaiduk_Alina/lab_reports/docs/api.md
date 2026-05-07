# API

## Аутентификация

- `POST /auth/register` - регистрация пользователя
- `POST /auth/login` - авторизация и выдача пары токенов (`access_token`, `refresh_token`)
- `POST /auth/refresh` - обновление пары токенов по `refresh_token`

## Пользователи

- `GET /users` - список пользователей
- `GET /users/{user_id}` - получение пользователя по id (доступ только к своему id)
- `PUT /users/{user_id}` - обновление пользователя (доступ только к своему id)
- `DELETE /users/{user_id}` - удаление пользователя (доступ только к своему id)
- `GET /users/{user_id}/with-tasks` - пользователь с задачами (доступ только к своему id)
- `POST /users/change-password` - смена пароля

## Категории

- `POST /categories`
- `GET /categories`
- `GET /categories/{category_id}`
- `PUT /categories/{category_id}`
- `DELETE /categories/{category_id}`

## Теги

- `POST /tags`
- `GET /tags`
- `GET /tags/{tag_id}`
- `PUT /tags/{tag_id}`
- `DELETE /tags/{tag_id}`

## Задания

- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{task_id}` - задача с категорией, тегами и логами времени
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `POST /tasks/{task_id}/tags` - привязка тега к задаче через `task_tags`
- `DELETE /tasks/{task_id}/tags/{tag_id}` - отвязка тега
- `GET /tasks/analytics/summary` - аналитика

### Фильтрация и сортировка задач

Поддержано в `GET /tasks`:

- фильтры: `status`, `priority`, `deadline_from`, `deadline_to`
- сортировка: `sort_by=deadline|priority|created_at`
- порядок: `sort_order=asc|desc`

## Time Logs

- `POST /time-logs`
- `GET /time-logs`
- `GET /time-logs/{time_log_id}`
- `PUT /time-logs/{time_log_id}`
- `DELETE /time-logs/{time_log_id}`

## Расписания

- `POST /schedules`
- `GET /schedules`
- `GET /schedules/day/{plan_date}` - расписание на день с задачами
- `GET /schedules/{schedule_id}`
- `PUT /schedules/{schedule_id}`
- `DELETE /schedules/{schedule_id}`

## Уведомления

- `POST /notifications`
- `GET /notifications`
- `GET /notifications/{notification_id}`
- `PUT /notifications/{notification_id}`
- `DELETE /notifications/{notification_id}`

## Проверка работы сервиса

- `GET /health` - проверка работоспособности API
