from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None
    estimated_minutes: int | None = None
    category_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None
    estimated_minutes: int | None = None
    category_id: int | None = None


class TaskShortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    deadline: datetime | None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class TaskTagCreate(BaseModel):
    tag_id: int
    weight: int = 1


class TaskTagLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tag_id: int
    task_id: int
    tagged_at: datetime
    weight: int
    tag: TagRead


class TaskWithRelationsRead(TaskRead):
    category: CategoryRead | None
    time_logs: list[TimeLogRead]
    tag_links: list[TaskTagLinkRead]


from app.schemas.category import CategoryRead
from app.schemas.tag import TagRead
from app.schemas.time_log import TimeLogRead

TaskTagLinkRead.model_rebuild()
TaskWithRelationsRead.model_rebuild()
