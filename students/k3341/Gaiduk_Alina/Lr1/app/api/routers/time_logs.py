from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.task import Task
from app.models.time_log import TimeLog
from app.models.user import User
from app.schemas.time_log import TimeLogCreate, TimeLogRead, TimeLogUpdate


router = APIRouter(prefix="/time-logs", tags=["time_logs"])


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user_id))


def _get_owned_time_log(db: Session, time_log_id: int, user_id: int) -> TimeLog | None:
    return db.scalar(
        select(TimeLog)
        .join(Task, Task.id == TimeLog.task_id)
        .where(TimeLog.id == time_log_id, Task.owner_id == user_id)
    )


def _validate_time_log_values(*, spent_minutes: int, started_at, ended_at) -> None:
    if spent_minutes <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="spent_minutes must be > 0")
    if ended_at <= started_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ended_at must be greater than started_at")
    interval_minutes = int((ended_at - started_at).total_seconds() // 60)
    if spent_minutes > interval_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spent_minutes cannot exceed time interval in minutes",
        )


@router.post("", response_model=TimeLogRead, status_code=status.HTTP_201_CREATED)
def create_time_log(
    payload: TimeLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimeLog:
    task = _get_owned_task(db=db, task_id=payload.task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    _validate_time_log_values(
        spent_minutes=payload.spent_minutes,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
    )

    time_log = TimeLog(**payload.model_dump())
    db.add(time_log)
    db.commit()
    db.refresh(time_log)
    return time_log


@router.get("", response_model=list[TimeLogRead])
def list_time_logs(
    task_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TimeLog]:
    stmt = select(TimeLog).join(Task, Task.id == TimeLog.task_id).where(Task.owner_id == current_user.id)
    if task_id is not None:
        stmt = stmt.where(TimeLog.task_id == task_id)
    stmt = stmt.order_by(TimeLog.id)
    return list(db.scalars(stmt).all())


@router.get("/{time_log_id}", response_model=TimeLogRead)
def get_time_log(
    time_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimeLog:
    time_log = _get_owned_time_log(db=db, time_log_id=time_log_id, user_id=current_user.id)
    if time_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time log not found")
    return time_log


@router.put("/{time_log_id}", response_model=TimeLogRead)
def update_time_log(
    time_log_id: int,
    payload: TimeLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TimeLog:
    time_log = _get_owned_time_log(db=db, time_log_id=time_log_id, user_id=current_user.id)
    if time_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time log not found")

    updates = payload.model_dump(exclude_unset=True)

    new_spent_minutes = updates.get("spent_minutes", time_log.spent_minutes)
    new_started_at = updates.get("started_at", time_log.started_at)
    new_ended_at = updates.get("ended_at", time_log.ended_at)
    _validate_time_log_values(
        spent_minutes=new_spent_minutes,
        started_at=new_started_at,
        ended_at=new_ended_at,
    )

    for key, value in updates.items():
        setattr(time_log, key, value)

    db.add(time_log)
    db.commit()
    db.refresh(time_log)
    return time_log


@router.delete("/{time_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_log(
    time_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    time_log = _get_owned_time_log(db=db, time_log_id=time_log_id, user_id=current_user.id)
    if time_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time log not found")

    db.delete(time_log)
    db.commit()
