from fastapi import FastAPI

from app.api.routers import auth, categories, notifications, schedules, tags, tasks, time_logs, users
from app.core.config import settings


app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(tasks.router)
app.include_router(time_logs.router)
app.include_router(schedules.router)
app.include_router(notifications.router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
