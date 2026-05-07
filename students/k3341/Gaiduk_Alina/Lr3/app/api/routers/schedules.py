from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.schedule import Schedule
from app.models.task import Task
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate, ScheduleWithTaskRead


router = APIRouter(prefix="/schedules", tags=["schedules"])


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user_id))


def _schedule_stmt(schedule_id: int, user_id: int):
    return select(Schedule).where(Schedule.id == schedule_id, Schedule.owner_id == user_id).options(joinedload(Schedule.task))


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Schedule:
    task = _get_owned_task(db=db, task_id=payload.task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    schedule = Schedule(**payload.model_dump(), owner_id=current_user.id)
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("", response_model=list[ScheduleRead])
def list_schedules(
    plan_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Schedule]:
    stmt = select(Schedule).where(Schedule.owner_id == current_user.id)
    if plan_date is not None:
        stmt = stmt.where(Schedule.plan_date == plan_date)
    stmt = stmt.order_by(Schedule.plan_date, Schedule.id)
    return list(db.scalars(stmt).all())


@router.get("/day/{plan_date}", response_model=list[ScheduleWithTaskRead])
def get_day_schedule(
    plan_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Schedule]:
    stmt = (
        select(Schedule)
        .where(Schedule.owner_id == current_user.id, Schedule.plan_date == plan_date)
        .options(joinedload(Schedule.task))
        .order_by(Schedule.id)
    )
    return list(db.scalars(stmt).all())


@router.get("/{schedule_id}", response_model=ScheduleWithTaskRead)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Schedule:
    schedule = db.scalar(_schedule_stmt(schedule_id=schedule_id, user_id=current_user.id))
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleRead)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Schedule:
    schedule = db.scalar(select(Schedule).where(Schedule.id == schedule_id, Schedule.owner_id == current_user.id))
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    updates = payload.model_dump(exclude_unset=True)
    if "task_id" in updates and updates["task_id"] is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task_id cannot be null")

    new_task_id = updates.get("task_id")
    if new_task_id is not None:
        task = _get_owned_task(db=db, task_id=new_task_id, user_id=current_user.id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for key, value in updates.items():
        setattr(schedule, key, value)

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    schedule = db.scalar(select(Schedule).where(Schedule.id == schedule_id, Schedule.owner_id == current_user.id))
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
