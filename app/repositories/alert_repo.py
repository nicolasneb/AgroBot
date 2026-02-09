import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: uuid.UUID, field_id: uuid.UUID,
        event_type: str, threshold: float
    ) -> Alert:
        alert = Alert(
            user_id=user_id, field_id=field_id,
            event_type=event_type, threshold=threshold
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        return await self.session.get(Alert, alert_id)

    async def get_active_alerts(self) -> list[Alert]:
        result = await self.session.execute(
            select(Alert).where(Alert.is_active == True)
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Alert]:
        result = await self.session.execute(
            select(Alert)
            .where(Alert.user_id == user_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, alert: Alert, **kwargs) -> Alert:
        for key, value in kwargs.items():
            if value is not None:
                setattr(alert, key, value)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def delete(self, alert: Alert) -> None:
        await self.session.delete(alert)
        await self.session.commit()