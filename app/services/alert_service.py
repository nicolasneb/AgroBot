import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertService:
    def __init__(self, session: AsyncSession):
        self.repo = AlertRepository(session)

    async def create_alert(self, data: AlertCreate) -> Alert:
        return await self.repo.create(
            user_id=data.user_id,
            field_id=data.field_id,
            event_type=data.event_type,
            threshold=data.threshold,
        )

    async def get_alert(self, alert_id: uuid.UUID) -> Alert | None:
        return await self.repo.get_by_id(alert_id)

    async def get_user_alerts(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Alert]:
        return await self.repo.get_by_user(user_id, skip=skip, limit=limit)

    async def update_alert(self, alert_id: uuid.UUID, data: AlertUpdate) -> Alert | None:
        alert = await self.repo.get_by_id(alert_id)
        if not alert:
            return None
        return await self.repo.update(
            alert,
            event_type=data.event_type,
            threshold=data.threshold,
            is_active=data.is_active,
        )

    async def delete_alert(self, alert_id: uuid.UUID) -> bool:
        alert = await self.repo.get_by_id(alert_id)
        if not alert:
            return False
        await self.repo.delete(alert)
        return True