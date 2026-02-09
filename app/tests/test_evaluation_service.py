from datetime import date
from unittest.mock import AsyncMock, patch

from app.repositories.user_repo import UserRepository
from app.repositories.field_repo import FieldRepository
from app.repositories.alert_repo import AlertRepository
from app.repositories.weather_repo import WeatherRepository
from app.services.evaluation_service import EvaluationService


async def test_evaluation_triggers_alert(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000030")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.0, longitude=-58.0,
    )

    weather_repo = WeatherRepository(session)
    today = date.today()
    await weather_repo.create(
        field_id=field.id, event_type="lluvia",
        probability=85.0, target_date=today,
    )

    alert_repo = AlertRepository(session)
    await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="lluvia", threshold=70.0,
    )

    with patch("app.services.evaluation_service.event_bus") as mock_bus, \
         patch("app.services.evaluation_service.flush_notifications", new_callable=AsyncMock) as mock_flush:
        mock_bus.emit = AsyncMock()
        service = EvaluationService(session)
        triggered = await service.evaluate_all()

        assert triggered >= 1
        mock_bus.emit.assert_called()
        mock_flush.assert_called_once()
        event = mock_bus.emit.call_args[0][0]
        assert event.event_type == "lluvia"
        assert event.actual_value == 85.0
        assert event.threshold == 70.0


async def test_evaluation_does_not_trigger_below_threshold(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000031")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.0, longitude=-58.0,
    )

    weather_repo = WeatherRepository(session)
    today = date.today()
    await weather_repo.create(
        field_id=field.id, event_type="lluvia",
        probability=30.0, target_date=today,
    )

    alert_repo = AlertRepository(session)
    await alert_repo.create(
        user_id=user.id, field_id=field.id,
        event_type="lluvia", threshold=70.0,
    )

    with patch("app.services.evaluation_service.event_bus") as mock_bus, \
         patch("app.services.evaluation_service.flush_notifications", new_callable=AsyncMock) as mock_flush:
        mock_bus.emit = AsyncMock()
        service = EvaluationService(session)
        triggered = await service.evaluate_all()

        assert triggered == 0
        mock_bus.emit.assert_not_called()
        mock_flush.assert_called_once()