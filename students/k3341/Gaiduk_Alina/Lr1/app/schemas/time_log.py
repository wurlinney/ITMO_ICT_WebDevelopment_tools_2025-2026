from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimeLogBase(BaseModel):
    spent_minutes: int = Field(gt=0)
    started_at: datetime
    ended_at: datetime
    comment: str | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "TimeLogBase":
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be greater than started_at")
        interval_minutes = int((self.ended_at - self.started_at).total_seconds() // 60)
        if self.spent_minutes > interval_minutes:
            raise ValueError("spent_minutes cannot exceed time interval in minutes")
        return self


class TimeLogCreate(TimeLogBase):
    task_id: int


class TimeLogUpdate(BaseModel):
    spent_minutes: int | None = Field(default=None, gt=0)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    comment: str | None = None


class TimeLogRead(TimeLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
