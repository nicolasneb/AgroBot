from unittest.mock import AsyncMock
from datetime import date
from uuid import uuid4

from app.events.event_bus import EventBus
from app.events.events import AlertTriggeredEvent


async def test_event_bus_emits_to_subscribers():
    bus = EventBus()
    handler = AsyncMock()
    bus.subscribe(AlertTriggeredEvent, handler)

    event = AlertTriggeredEvent(
        alert_id=uuid4(), user_id=uuid4(), field_id=uuid4(),
        event_type="lluvia", threshold=70.0,
        actual_value=85.0, target_date=date.today(),
    )

    await bus.emit(event)
    handler.assert_called_once_with(event)


async def test_event_bus_multiple_handlers():
    bus = EventBus()
    handler1 = AsyncMock()
    handler2 = AsyncMock()
    bus.subscribe(AlertTriggeredEvent, handler1)
    bus.subscribe(AlertTriggeredEvent, handler2)

    event = AlertTriggeredEvent(
        alert_id=uuid4(), user_id=uuid4(), field_id=uuid4(),
        event_type="helada", threshold=50.0,
        actual_value=65.0, target_date=date.today(),
    )

    await bus.emit(event)
    handler1.assert_called_once_with(event)
    handler2.assert_called_once_with(event)


async def test_event_bus_no_handlers():
    bus = EventBus()
    event = AlertTriggeredEvent(
        alert_id=uuid4(), user_id=uuid4(), field_id=uuid4(),
        event_type="granizo", threshold=80.0,
        actual_value=90.0, target_date=date.today(),
    )

    await bus.emit(event)