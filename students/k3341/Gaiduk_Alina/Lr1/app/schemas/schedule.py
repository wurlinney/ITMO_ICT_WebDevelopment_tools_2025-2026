from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class ScheduleBase(BaseModel):
    task_id: int
    plan_date: date
    note: str | None = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    task_id: int | None = None
    plan_date: date | None = None
    note: str | None = None


class ScheduleRead(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int


class ScheduleWithTaskRead(ScheduleRead):
    task: TaskShortRead


from app.schemas.task import TaskShortRead

ScheduleWithTaskRead.model_rebuild()
