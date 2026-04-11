from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationRead, NotificationUpdate


router = APIRouter(prefix="/notifications", tags=["notifications"])


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == user_id))


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Notification:
    if payload.task_id is not None:
        task = _get_owned_task(db=db, task_id=payload.task_id, user_id=current_user.id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    notification = Notification(**payload.model_dump(), owner_id=current_user.id)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[Notification]:
    stmt = select(Notification).where(Notification.owner_id == current_user.id).order_by(Notification.id)
    return list(db.scalars(stmt).all())


@router.get("/{notification_id}", response_model=NotificationRead)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.owner_id == current_user.id)
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.put("/{notification_id}", response_model=NotificationRead)
def update_notification(
    notification_id: int,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.owner_id == current_user.id)
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(notification, key, value)

    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    notification = db.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.owner_id == current_user.id)
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db.delete(notification)
    db.commit()
