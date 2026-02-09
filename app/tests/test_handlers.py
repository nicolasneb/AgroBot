import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import logging
from uuid import uuid4
from datetime import date
from unittest.mock import patch, AsyncMock, MagicMock

from app.events.events import AlertTriggeredEvent
from app.events.handlers.notification_handler import (
    handle_alert_triggered,
    flush_notifications,
    _pending_notifications,
)


@pytest.fixture(autouse=True)
def clear_pending():
    _pending_notifications.clear()
    yield
    _pending_notifications.clear()


async def test_handle_alert_triggered_appends_to_pending():
    event = AlertTriggeredEvent(
        alert_id=uuid4(),
        user_id=uuid4(),
        field_id=uuid4(),
        event_type="frost",
        threshold=80.0,
        actual_value=90.0,
        target_date=date(2025, 1, 15),
    )

    await handle_alert_triggered(event)

    assert len(_pending_notifications) == 1
    notif = _pending_notifications[0]
    assert notif["user_id"] == event.user_id
    assert notif["alert_id"] == event.alert_id
    assert "frost" in notif["message"]
    assert "90.0%" in notif["message"]


async def test_handle_alert_triggered_accumulates_multiple():
    for i in range(3):
        event = AlertTriggeredEvent(
            alert_id=uuid4(),
            user_id=uuid4(),
            field_id=uuid4(),
            event_type=f"event_{i}",
            threshold=50.0,
            actual_value=70.0 + i,
            target_date=date(2025, 1, 15),
        )
        await handle_alert_triggered(event)

    assert len(_pending_notifications) == 3


async def test_flush_notifications_calls_bulk_create():
    event = AlertTriggeredEvent(
        alert_id=uuid4(),
        user_id=uuid4(),
        field_id=uuid4(),
        event_type="hail",
        threshold=50.0,
        actual_value=65.0,
        target_date=date(2025, 2, 10),
    )
    await handle_alert_triggered(event)
    assert len(_pending_notifications) == 1

    mock_repo_instance = AsyncMock()
    mock_repo_instance.bulk_create = AsyncMock()

    # Mock async context manager para async_session
    mock_session = AsyncMock()
    mock_async_session = MagicMock()
    mock_async_session.return_value = AsyncMock(
        __aenter__=AsyncMock(return_value=mock_session),
        __aexit__=AsyncMock(return_value=False),
    )

    import app.repositories.notification_repo as repo_mod
    import app.events.handlers.notification_handler as handler_mod

    original_class = repo_mod.NotificationRepository
    original_session = handler_mod.async_session

    repo_mod.NotificationRepository = MagicMock(return_value=mock_repo_instance)
    handler_mod.async_session = mock_async_session

    try:
        count = await flush_notifications()
    finally:
        repo_mod.NotificationRepository = original_class
        handler_mod.async_session = original_session

    assert count == 1
    mock_repo_instance.bulk_create.assert_called_once()

    # Re-importar para ver el estado actual del módulo
    from app.events.handlers.notification_handler import _pending_notifications as current
    assert len(current) == 0


async def test_flush_notifications_empty_noop():
    count = await flush_notifications()
    assert count == 0


async def test_flush_notifications_logs(caplog):
    event = AlertTriggeredEvent(
        alert_id=uuid4(),
        user_id=uuid4(),
        field_id=uuid4(),
        event_type="hail",
        threshold=50.0,
        actual_value=65.0,
        target_date=date(2025, 2, 10),
    )
    await handle_alert_triggered(event)

    mock_repo_instance = AsyncMock()
    mock_repo_instance.bulk_create = AsyncMock()

    mock_session = AsyncMock()
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.events.handlers.notification_handler.async_session", return_value=mock_session_cm):
        import app.repositories.notification_repo as repo_mod
        original_class = repo_mod.NotificationRepository
        repo_mod.NotificationRepository = MagicMock(return_value=mock_repo_instance)
        try:
            with caplog.at_level(logging.INFO):
                await flush_notifications()
        finally:
            repo_mod.NotificationRepository = original_class

    assert any("Bulk insert" in record.message for record in caplog.records)