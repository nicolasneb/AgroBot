import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.config import settings

TEST_DATABASE_URL = settings.TEST_DATABASE_URL or (
    settings.DATABASE_URL.rsplit("/", 1)[0] + "/agrobot_test"
)

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=__import__("sqlalchemy.pool", fromlist=["NullPool"]).NullPool,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as sess:
        yield sess
        await sess.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


def get_test_session_factory():
    return async_session_factory