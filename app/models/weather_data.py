import uuid
from datetime import date, datetime

from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WeatherData(Base):
    __tablename__ = "weather_data"
    __table_args__ = (
        Index("ix_weather_field_event_date", "field_id", "event_type", "target_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="weather_data")