import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.notification import Notification
from app.repositories.notification_repo import NotificationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/user/{user_id}", response_model=list[NotificationResponse])
async def get_user_notifications(
    user_id: uuid.UUID,
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    repo = NotificationRepository(session)
    return await repo.get_by_user(user_id, unread_only=unread_only, skip=skip, limit=limit)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    notification = await session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    repo = NotificationRepository(session)
    return await repo.mark_as_read(notification)