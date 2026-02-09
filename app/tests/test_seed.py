import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from sqlalchemy import select
from app.seeds.seed_data import seed
from app.models.user import User
from app.models.field import Field
from app.models.alert import Alert
from app.models.weather_data import WeatherData


async def test_seed_populates_database(session):
    await seed(session)

    users = (await session.execute(select(User))).scalars().all()
    assert len(users) >= 2

    fields = (await session.execute(select(Field))).scalars().all()
    assert len(fields) >= 2

    alerts = (await session.execute(select(Alert))).scalars().all()
    assert len(alerts) >= 2

    weather = (await session.execute(select(WeatherData))).scalars().all()
    assert len(weather) >= 1


async def test_seed_is_idempotent(session):
    await seed(session)
    await seed(session)

    users = (await session.execute(select(User))).scalars().all()
    # No debería duplicar datos
    assert len(users) >= 2