from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class UserWithTasksRead(UserRead):
    tasks: list[TaskShortRead]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


from app.schemas.task import TaskShortRead

UserWithTasksRead.model_rebuild()
