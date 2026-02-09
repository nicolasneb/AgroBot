import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    user_id: uuid.UUID
    field_id: uuid.UUID
    event_type: str
    threshold: float = Field(ge=0, le=100)


class AlertUpdate(BaseModel):
    event_type: str | None = None
    threshold: float | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    field_id: uuid.UUID
    event_type: str
    threshold: float
    is_active: bool
    created_at: datetime