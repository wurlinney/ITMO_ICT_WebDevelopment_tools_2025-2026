from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.category import Category
from app.models.enums import TaskPriority, TaskStatus
from app.models.tag import Tag
from app.models.task import Task
from app.models.task_tag import TaskTag
from app.models.time_log import TimeLog
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskTagCreate, TaskUpdate, TaskWithRelationsRead


router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user_id))


def _build_task_with_relations_stmt(task_id: int, user_id: int):
    return (
        select(Task)
        .where(Task.id == task_id, Task.owner_id == user_id)
        .options(
            joinedload(Task.category),
            selectinload(Task.time_logs),
            selectinload(Task.tag_links).joinedload(TaskTag.tag),
        )
    )


@router.get("/analytics/summary")
def task_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    spent_by_task_rows = db.execute(
        select(
            Task.id,
            Task.title,
            func.coalesce(func.sum(TimeLog.spent_minutes), 0).label("spent_minutes"),
        )
        .outerjoin(TimeLog, TimeLog.task_id == Task.id)
        .where(Task.owner_id == current_user.id)
        .group_by(Task.id, Task.title)
        .order_by(Task.id)
    ).all()

    spent_by_category_rows = db.execute(
        select(
            Category.id,
            Category.name,
            func.coalesce(func.sum(TimeLog.spent_minutes), 0).label("spent_minutes"),
        )
        .outerjoin(Task, Task.category_id == Category.id)
        .outerjoin(TimeLog, TimeLog.task_id == Task.id)
        .where(Category.owner_id == current_user.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.id)
    ).all()

    overdue_count = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.owner_id == current_user.id,
            Task.deadline.is_not(None),
            Task.deadline < datetime.now(UTC),
            Task.status != TaskStatus.DONE,
        )
    )

    return {
        "spent_by_tasks": [
            {"task_id": row.id, "title": row.title, "spent_minutes": int(row.spent_minutes)} for row in spent_by_task_rows
        ],
        "spent_by_categories": [
            {
                "category_id": row.id,
                "category_name": row.name,
                "spent_minutes": int(row.spent_minutes),
            }
            for row in spent_by_category_rows
        ],
        "overdue_tasks_count": int(overdue_count or 0),
    }


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Task:
    if payload.category_id is not None:
        category = db.scalar(
            select(Category).where(Category.id == payload.category_id, Category.owner_id == current_user.id)
        )
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    task = Task(**payload.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    priority_filter: str | None = Query(default=None, alias="priority"),
    deadline_from: datetime | None = None,
    deadline_to: datetime | None = None,
    sort_by: str = Query(default="deadline"),
    sort_order: str = Query(default="asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Task]:
    stmt = select(Task).where(Task.owner_id == current_user.id)

    if status_filter is not None:
        try:
            status_value = TaskStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter") from exc
        stmt = stmt.where(Task.status == status_value)

    if priority_filter is not None:
        try:
            priority_value = TaskPriority(priority_filter)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority filter") from exc
        stmt = stmt.where(Task.priority == priority_value)

    if deadline_from is not None:
        stmt = stmt.where(Task.deadline.is_not(None), Task.deadline >= deadline_from)

    if deadline_to is not None:
        stmt = stmt.where(Task.deadline.is_not(None), Task.deadline <= deadline_to)

    if sort_by == "deadline":
        order_expr = Task.deadline
    elif sort_by == "priority":
        order_expr = case(
            (Task.priority == TaskPriority.LOW, 1),
            (Task.priority == TaskPriority.MEDIUM, 2),
            (Task.priority == TaskPriority.HIGH, 3),
            else_=4,
        )
    elif sort_by == "created_at":
        order_expr = Task.created_at
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_order")

    if sort_order == "desc":
        stmt = stmt.order_by(desc(order_expr), Task.id)
    else:
        stmt = stmt.order_by(order_expr, Task.id)

    return list(db.scalars(stmt).all())


@router.get("/{task_id}", response_model=TaskWithRelationsRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Task:
    task = db.scalar(_build_task_with_relations_stmt(task_id=task_id, user_id=current_user.id))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Task:
    task = _get_owned_task(db=db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    new_category_id = updates.get("category_id")
    if new_category_id is not None:
        category = db.scalar(select(Category).where(Category.id == new_category_id, Category.owner_id == current_user.id))
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for key, value in updates.items():
        setattr(task, key, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    task = _get_owned_task(db=db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()


@router.post("/{task_id}/tags", response_model=TaskWithRelationsRead)
def attach_tag_to_task(
    task_id: int,
    payload: TaskTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Task:
    task = _get_owned_task(db=db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    tag = db.scalar(select(Tag).where(Tag.id == payload.tag_id))
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    existing = db.scalar(select(TaskTag).where(TaskTag.task_id == task_id, TaskTag.tag_id == payload.tag_id))
    if existing:
        existing.weight = payload.weight
        db.add(existing)
    else:
        db.add(TaskTag(task_id=task_id, tag_id=payload.tag_id, weight=payload.weight))

    db.commit()

    task_with_relations = db.scalar(_build_task_with_relations_stmt(task_id=task_id, user_id=current_user.id))
    if task_with_relations is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_with_relations


@router.delete("/{task_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag_from_task(
    task_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    task = _get_owned_task(db=db, task_id=task_id, user_id=current_user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    link = db.scalar(select(TaskTag).where(TaskTag.task_id == task_id, TaskTag.tag_id == tag_id))
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TaskTag link not found")

    db.delete(link)
    db.commit()
