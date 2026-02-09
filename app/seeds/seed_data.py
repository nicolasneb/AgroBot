import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.field import Field
from app.models.weather_data import WeatherData
from app.models.alert import Alert

logger = logging.getLogger(__name__)


async def seed(session: AsyncSession):
    # Verificar si ya hay datos
    result = await session.execute(select(User))
    if result.scalars().first():
        logger.info("📦 Seed: datos ya existentes, saltando...")
        return

    logger.info("🌱 Seed: cargando datos mock...")

    # ── Usuarios ──
    user1 = User(name="Juan Pérez", phone="+5491112345678")
    user2 = User(name="María García", phone="+5491187654321")
    session.add_all([user1, user2])
    await session.flush()

    # ── Campos ──
    field1 = Field(
        user_id=user1.id, name="Campo La Esperanza",
        latitude=-34.6037, longitude=-58.3816,
    )
    field2 = Field(
        user_id=user1.id, name="Campo El Progreso",
        latitude=-33.4489, longitude=-60.6693,
    )
    field3 = Field(
        user_id=user2.id, name="Campo San Martín",
        latitude=-32.9468, longitude=-60.6393,
    )
    session.add_all([field1, field2, field3])
    await session.flush()

    # ── Datos meteorológicos (próximos 7 días) ──
    today = date.today()
    weather_entries = []

    # Campo 1 - lluvia alta, helada baja
    for i in range(7):
        target = today + timedelta(days=i)
        weather_entries.append(WeatherData(
            field_id=field1.id, event_type="lluvia",
            probability=70.0 + i * 3, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field1.id, event_type="helada",
            probability=10.0 + i * 2, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field1.id, event_type="granizo",
            probability=5.0 + i, target_date=target,
        ))

    # Campo 2 - helada alta, lluvia baja
    for i in range(7):
        target = today + timedelta(days=i)
        weather_entries.append(WeatherData(
            field_id=field2.id, event_type="lluvia",
            probability=20.0 + i * 2, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field2.id, event_type="helada",
            probability=60.0 + i * 5, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field2.id, event_type="granizo",
            probability=15.0 + i * 3, target_date=target,
        ))

    # Campo 3 - granizo alto
    for i in range(7):
        target = today + timedelta(days=i)
        weather_entries.append(WeatherData(
            field_id=field3.id, event_type="lluvia",
            probability=30.0 + i, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field3.id, event_type="helada",
            probability=25.0 + i * 2, target_date=target,
        ))
        weather_entries.append(WeatherData(
            field_id=field3.id, event_type="granizo",
            probability=55.0 + i * 6, target_date=target,
        ))

    session.add_all(weather_entries)
    await session.flush()

    # ── Alertas ──
    alerts = [
        Alert(
            user_id=user1.id, field_id=field1.id,
            event_type="lluvia", threshold=65.0,
        ),
        Alert(
            user_id=user1.id, field_id=field2.id,
            event_type="helada", threshold=50.0,
        ),
        Alert(
            user_id=user2.id, field_id=field3.id,
            event_type="granizo", threshold=80.0,
        ),
        Alert(
            user_id=user2.id, field_id=field3.id,
            event_type="lluvia", threshold=90.0,
        ),
    ]
    session.add_all(alerts)

    await session.commit()
    logger.info("✅ Seed: datos mock cargados exitosamente")
    logger.info("   - 2 usuarios")
    logger.info("   - 3 campos")
    logger.info("   - 63 registros meteorológicos (7 días x 3 eventos x 3 campos)")
    logger.info("   - 4 alertas (3 se van a disparar, 1 no)")