import asyncio
import logging

from app.config import settings
from app.database import async_session
from app.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)


async def run_evaluation_job():
    """
    Background job que evalúa periódicamente las alertas activas
    contra los datos meteorológicos almacenados.
    Se ejecuta cada EVALUATION_INTERVAL_SECONDS (default: 60s).
    """
    while True:
        try:
            logger.info("⏰ Job de evaluación iniciado")
            async with async_session() as session:
                service = EvaluationService(session)
                triggered = await service.evaluate_all()
                logger.info(f"✅ Job finalizado. Alertas disparadas: {triggered}")
        except Exception as e:
            logger.error(f"❌ Error en job de evaluación: {e}")

        await asyncio.sleep(settings.EVALUATION_INTERVAL_SECONDS)