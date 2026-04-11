from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    message: str
    due_at: datetime | None = None


class NotificationCreate(NotificationBase):
    task_id: int | None = None


class NotificationUpdate(BaseModel):
    message: str | None = None
    due_at: datetime | None = None
    is_sent: bool | None = None


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    task_id: int | None
    is_sent: bool
    created_at: datetime
