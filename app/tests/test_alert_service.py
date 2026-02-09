import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from uuid import uuid4

from app.models.user import User
from app.models.field import Field
from app.services.alert_service import AlertService
from app.schemas.alert import AlertCreate, AlertUpdate


async def _create_user_and_field(session):
    user = User(name="Svc User", phone="+5491100000099")
    session.add(user)
    await session.flush()

    field = Field(name="Svc Field", latitude=-31.4, longitude=-64.2, user_id=user.id)
    session.add(field)
    await session.flush()
    return user, field


async def test_create_alert_via_service(session):
    user, field = await _create_user_and_field(session)
    service = AlertService(session)

    data = AlertCreate(user_id=user.id, field_id=field.id, event_type="frost", threshold=80.0)
    alert = await service.create_alert(data)
    assert alert.event_type == "frost"
    assert alert.is_active is True


async def test_get_alert_by_id_via_service(session):
    user, field = await _create_user_and_field(session)
    service = AlertService(session)

    data = AlertCreate(user_id=user.id, field_id=field.id, event_type="hail", threshold=50.0)
    created = await service.create_alert(data)
    found = await service.get_alert(created.id)
    assert found is not None
    assert found.id == created.id


async def test_get_user_alerts_via_service(session):
    user, field = await _create_user_and_field(session)
    service = AlertService(session)

    await service.create_alert(AlertCreate(user_id=user.id, field_id=field.id, event_type="frost", threshold=80.0))
    await service.create_alert(AlertCreate(user_id=user.id, field_id=field.id, event_type="drought", threshold=60.0))

    alerts = await service.get_user_alerts(user.id)
    assert len(alerts) >= 2


async def test_delete_alert_via_service(session):
    user, field = await _create_user_and_field(session)
    service = AlertService(session)

    data = AlertCreate(user_id=user.id, field_id=field.id, event_type="flood", threshold=70.0)
    alert = await service.create_alert(data)
    result = await service.delete_alert(alert.id)
    assert result is True

    found = await service.get_alert(alert.id)
    assert found is None