from app.repositories.user_repo import UserRepository
from app.repositories.field_repo import FieldRepository
from app.repositories.alert_repo import AlertRepository


async def test_create_alert(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000020")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.0, longitude=-58.0,
    )

    alert_repo = AlertRepository(session)
    alert = await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="lluvia", threshold=70.0,
    )

    assert alert.id is not None
    assert alert.event_type == "lluvia"
    assert alert.threshold == 70.0
    assert alert.is_active is True


async def test_get_active_alerts(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000021")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.0, longitude=-58.0,
    )

    alert_repo = AlertRepository(session)
    await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="lluvia", threshold=70.0,
    )
    alert2 = await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="helada", threshold=50.0,
    )
    await alert_repo.update(alert2, is_active=False)

    active = await alert_repo.get_active_alerts()
    assert len(active) == 1
    assert active[0].event_type == "lluvia"


async def test_delete_alert(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000022")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.0, longitude=-58.0,
    )

    alert_repo = AlertRepository(session)
    alert = await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="lluvia", threshold=70.0,
    )

    await alert_repo.delete(alert)
    found = await alert_repo.get_by_id(alert.id)
    assert found is None