import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from app.models.user import User
from app.models.field import Field
from app.models.alert import Alert
from app.repositories.notification_repo import NotificationRepository


async def _setup_alert(session):
    user = User(name="Notif User", phone="+5491100000050")
    session.add(user)
    await session.flush()

    field = Field(name="Notif Field", latitude=-31.0, longitude=-64.0, user_id=user.id)
    session.add(field)
    await session.flush()

    alert = Alert(user_id=user.id, field_id=field.id, event_type="frost", threshold=80.0)
    session.add(alert)
    await session.flush()

    return user, alert


async def test_create_notification(session):
    user, alert = await _setup_alert(session)
    repo = NotificationRepository(session)
    notif = await repo.create(user_id=user.id, alert_id=alert.id, message="Test notification")
    assert notif.message == "Test notification"
    assert notif.is_read is False


async def test_get_by_user(session):
    user, alert = await _setup_alert(session)
    repo = NotificationRepository(session)
    await repo.create(user_id=user.id, alert_id=alert.id, message="Notif 1")
    await repo.create(user_id=user.id, alert_id=alert.id, message="Notif 2")

    results = await repo.get_by_user(user.id)
    assert len(results) == 2


async def test_get_by_user_unread_only(session):
    user, alert = await _setup_alert(session)
    repo = NotificationRepository(session)
    n1 = await repo.create(user_id=user.id, alert_id=alert.id, message="Unread")
    n2 = await repo.create(user_id=user.id, alert_id=alert.id, message="Read")
    await repo.mark_as_read(n2)

    unread = await repo.get_by_user(user.id, unread_only=True)
    assert len(unread) == 1
    assert unread[0].message == "Unread"


async def test_mark_as_read(session):
    user, alert = await _setup_alert(session)
    repo = NotificationRepository(session)
    notif = await repo.create(user_id=user.id, alert_id=alert.id, message="To read")
    assert notif.is_read is False

    updated = await repo.mark_as_read(notif)
    assert updated.is_read is True