from dataclasses import dataclass
from uuid import UUID
from datetime import date


@dataclass
class AlertTriggeredEvent:
    alert_id: UUID
    user_id: UUID
    field_id: UUID
    event_type: str
    threshold: float
    actual_value: float
    target_date: date