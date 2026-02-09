import logging
from datetime import date, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.event_bus import event_bus
from app.events.events import AlertTriggeredEvent
from app.events.handlers.notification_handler import flush_notifications
from app.models.alert import Alert
from app.models.weather_data import WeatherData

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def evaluate_all(self):
        logger.info("Iniciando evaluación de alertas...")

        today = date.today()
        end_date = today + timedelta(days=7)

        query = (
            select(Alert, WeatherData)
            .join(
                WeatherData,
                and_(
                    WeatherData.field_id == Alert.field_id,
                    WeatherData.event_type == Alert.event_type,
                    WeatherData.probability >= Alert.threshold,
                    WeatherData.target_date >= today,
                    WeatherData.target_date < end_date,
                ),
            )
            .where(Alert.is_active == True)
        )

        result = await self.session.execute(query)
        rows = result.all()

        triggered = 0
        for alert, weather in rows:
            await event_bus.emit(
                AlertTriggeredEvent(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    field_id=alert.field_id,
                    event_type=alert.event_type,
                    threshold=alert.threshold,
                    actual_value=weather.probability,
                    target_date=weather.target_date,
                )
            )
            triggered += 1

        # Bulk insert de todas las notificaciones acumuladas
        await flush_notifications()

        logger.info(f"Evaluación finalizada. Alertas disparadas: {triggered}")
        return triggered