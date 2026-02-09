import logging

from app.events.events import AlertTriggeredEvent

logger = logging.getLogger(__name__)


async def handle_alert_triggered_log(event: AlertTriggeredEvent):
    logger.warning(
        f"🔔 Umbral superado | "
        f"Evento: {event.event_type} | "
        f"Campo: {event.field_id} | "
        f"Usuario: {event.user_id} | "
        f"Valor: {event.actual_value}% > Umbral: {event.threshold}% | "
        f"Fecha: {event.target_date}"
    )