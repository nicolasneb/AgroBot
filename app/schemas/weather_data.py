import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WeatherDataCreate(BaseModel):
    field_id: uuid.UUID
    event_type: str
    probability: float = Field(ge=0, le=100)
    target_date: date


class WeatherDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_id: uuid.UUID
    event_type: str
    probability: float
    target_date: date
    created_at: datetime