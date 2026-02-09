import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.field import Field


class FieldRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, name: str, latitude: float, longitude: float) -> Field:
        field = Field(user_id=user_id, name=name, latitude=latitude, longitude=longitude)
        self.session.add(field)
        await self.session.commit()
        await self.session.refresh(field)
        return field

    async def get_by_id(self, field_id: uuid.UUID) -> Field | None:
        return await self.session.get(Field, field_id)

    async def get_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Field]:
        result = await self.session.execute(
            select(Field)
            .where(Field.user_id == user_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())