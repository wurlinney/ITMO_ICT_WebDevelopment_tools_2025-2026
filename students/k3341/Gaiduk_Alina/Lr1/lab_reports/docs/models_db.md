# Модели

### Пользователи (`users`)

- `id`, `email`, `full_name`, `hashed_password`, `is_active`, `created_at`
- связи: `tasks`, `categories`, `schedules`, `notifications`

### Категории (`categories`)

- `id`, `name`, `owner_id`
- связи: `owner`, `tasks`

### Задания (`tasks`)

- `id`, `title`, `description`, `status`, `priority`, `deadline`, `estimated_minutes`, `owner_id`, `category_id`, `created_at`, `updated_at`
- связи: `owner`, `category`, `time_logs`, `tag_links`

### Теги (`tags`)

- `id`, `name`, `created_at`
- связи: `task_links`

### Теги задания (`task_tags`)

- `task_id`, `tag_id`, `tagged_at`, `weight`
- связи: `task`, `tag`

### TimeLog (`time_logs`)

- `id`, `task_id`, `spent_minutes`, `started_at`, `ended_at`, `comment`
- связь: `task`

### Расписания (`schedules`)

- `id`, `owner_id`, `task_id`, `plan_date`, `note`
- связи: `owner`, `task`

### Уведоммления (`notifications`)

- `id`, `owner_id`, `task_id`, `message`, `due_at`, `is_sent`, `created_at`
- связи: `owner`, `task`

