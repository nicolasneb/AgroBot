import logging

from app.database import async_session
from app.events.events import AlertTriggeredEvent

logger = logging.getLogger(__name__)

_pending_notifications: list[dict] = []


async def handle_alert_triggered(event: AlertTriggeredEvent):
    message = (
        f"⚠️ Alerta: {event.event_type} detectada con "
        f"{event.actual_value}% de probabilidad "
        f"(umbral configurado: {event.threshold}%) "
        f"para el día {event.target_date}"
    )
    _pending_notifications.append({
        "user_id": event.user_id,
        "alert_id": event.alert_id,
        "message": message,
    })


async def flush_notifications():
    """Inserta todas las notificaciones pendientes en un solo batch."""
    global _pending_notifications
    if not _pending_notifications:
        return 0

    from app.repositories.notification_repo import NotificationRepository

    async with async_session() as session:
        repo = NotificationRepository(session)
        await repo.bulk_create(_pending_notifications)
        count = len(_pending_notifications)
        _pending_notifications = []
        logger.info(f"Bulk insert: {count} notificaciones creadas")
        return count