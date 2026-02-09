import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FieldCreate(BaseModel):
    user_id: uuid.UUID
    name: str
    latitude: float
    longitude: float


class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    latitude: float
    longitude: float
    created_at: datetime