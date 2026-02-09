import uuid
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather_data import WeatherData


class WeatherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, field_id: uuid.UUID, event_type: str, probability: float, target_date: date) -> WeatherData:
        weather = WeatherData(
            field_id=field_id, event_type=event_type,
            probability=probability, target_date=target_date
        )
        self.session.add(weather)
        await self.session.commit()
        await self.session.refresh(weather)
        return weather

    async def get_by_field_and_event(
        self, field_id: uuid.UUID, event_type: str, target_date: date
    ) -> WeatherData | None:
        result = await self.session.execute(
            select(WeatherData).where(
                and_(
                    WeatherData.field_id == field_id,
                    WeatherData.event_type == event_type,
                    WeatherData.target_date == target_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_field(self, field_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[WeatherData]:
        result = await self.session.execute(
            select(WeatherData)
            .where(WeatherData.field_id == field_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())