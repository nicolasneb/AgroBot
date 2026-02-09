import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import async_session
from app.events.event_bus import event_bus
from app.events.events import AlertTriggeredEvent
from app.events.handlers.notification_handler import handle_alert_triggered
from app.events.handlers.log_handler import handle_alert_triggered_log
from app.jobs.evaluate_alerts import run_evaluation_job
from app.routers import users, fields, alerts, notifications, weather
from app.seeds.seed_data import seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registrar handlers del Observer
    event_bus.subscribe(AlertTriggeredEvent, handle_alert_triggered)
    event_bus.subscribe(AlertTriggeredEvent, handle_alert_triggered_log)
    logger.info("🔔 Event handlers registrados")

    # Cargar datos mock
    async with async_session() as session:
        await seed(session)

    # Lanzar background job
    task = asyncio.create_task(run_evaluation_job())
    logger.info("🚀 Background job de evaluación iniciado")

    yield

    task.cancel()
    logger.info("🛑 Background job detenido")


app = FastAPI(
    title="Agrobot - Sistema de Alertas Climáticas",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(fields.router)
app.include_router(alerts.router)
app.include_router(notifications.router)
app.include_router(weather.router)


@app.get("/")
async def root():
    return {"message": "Hola Mundo 🌾 - Agrobot Alertas Climáticas"}


@app.get("/health")
async def health():
    return {"status": "ok"}