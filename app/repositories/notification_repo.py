import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: uuid.UUID, alert_id: uuid.UUID, message: str
    ) -> Notification:
        notification = Notification(
            user_id=user_id, alert_id=alert_id, message=message
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def bulk_create(self, notifications_data: list[dict]) -> None:
        notifications = [Notification(**data) for data in notifications_data]
        self.session.add_all(notifications)
        await self.session.commit()

    async def get_by_user(
        self, user_id: uuid.UUID, unread_only: bool = False,
        skip: int = 0, limit: int = 20
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        result = await self.session.execute(
            query.order_by(Notification.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        await self.session.commit()
        await self.session.refresh(notification)
        return notification