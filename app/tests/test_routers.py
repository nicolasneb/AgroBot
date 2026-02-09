import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import httpx
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_session
from app.config import settings

TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/agrobot_test"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=__import__("sqlalchemy.pool", fromlist=["NullPool"]).NullPool,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session():
    async with async_session_factory() as sess:
        yield sess


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ─── HELPERS ───

async def create_user(client, phone="+5491100000010"):
    resp = await client.post("/users/", json={"name": "Owner", "phone": phone})
    return resp.json()["id"]


async def create_field(client, phone="+5491100000020"):
    user_id = await create_user(client, phone=phone)
    resp = await client.post("/fields/", json={
        "name": "F1", "latitude": -31.0, "longitude": -64.0, "user_id": str(user_id)
    })
    return resp.json()["id"]


async def create_alert_data(client, phone="+5491100000030"):
    user_id = await create_user(client, phone=phone)
    field_resp = await client.post("/fields/", json={
        "name": "F1", "latitude": -31.0, "longitude": -64.0, "user_id": str(user_id)
    })
    field_id = field_resp.json()["id"]
    return user_id, field_id


FAKE_ID = str(uuid4())


# ─── USERS ───

async def test_create_user(client):
    resp = await client.post("/users/", json={"name": "Test User", "phone": "+5491112345678"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test User"
    assert "id" in data


async def test_create_user_duplicate_phone(client):
    await client.post("/users/", json={"name": "User1", "phone": "+5491100099999"})
    resp = await client.post("/users/", json={"name": "User2", "phone": "+5491100099999"})
    assert resp.status_code == 409


async def test_get_users(client):
    await client.post("/users/", json={"name": "User1", "phone": "+5491100000001"})
    await client.post("/users/", json={"name": "User2", "phone": "+5491100000002"})
    resp = await client.get("/users/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_get_users_pagination(client):
    for i in range(5):
        await client.post("/users/", json={"name": f"User{i}", "phone": f"+549110000{i:04d}"})

    resp = await client.get("/users/?skip=0&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/users/?skip=2&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/users/?skip=4&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_users_pagination_invalid_params(client):
    resp = await client.get("/users/?skip=-1")
    assert resp.status_code == 422

    resp = await client.get("/users/?limit=0")
    assert resp.status_code == 422

    resp = await client.get("/users/?limit=101")
    assert resp.status_code == 422


async def test_get_user_by_id(client):
    create = await client.post("/users/", json={"name": "Find Me", "phone": "+5491100000003"})
    user_id = create.json()["id"]
    resp = await client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Find Me"


async def test_get_user_not_found(client):
    resp = await client.get(f"/users/{FAKE_ID}")
    assert resp.status_code == 404


# ─── FIELDS ───

async def test_create_field(client):
    user_id = await create_user(client, phone="+5491100000040")
    resp = await client.post("/fields/", json={
        "name": "Campo Norte",
        "latitude": -31.4,
        "longitude": -64.2,
        "user_id": str(user_id)
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Campo Norte"


async def test_create_field_user_not_found(client):
    resp = await client.post("/fields/", json={
        "name": "Campo Fantasma",
        "latitude": -31.0,
        "longitude": -64.0,
        "user_id": FAKE_ID
    })
    assert resp.status_code == 404


async def test_get_fields(client):
    user_id = await create_user(client, phone="+5491100000050")
    resp = await client.post("/fields/", json={
        "name": "F1", "latitude": -31.0, "longitude": -64.0, "user_id": str(user_id)
    })
    field_id = resp.json()["id"]
    resp = await client.get(f"/fields/{field_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "F1"


async def test_get_field_not_found(client):
    resp = await client.get(f"/fields/{FAKE_ID}")
    assert resp.status_code == 404


async def test_get_fields_by_user(client):
    user_id = await create_user(client, phone="+5491100000060")
    await client.post("/fields/", json={
        "name": "F1", "latitude": -31.0, "longitude": -64.0, "user_id": str(user_id)
    })
    resp = await client.get(f"/fields/user/{user_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_fields_by_user_pagination(client):
    user_id = await create_user(client, phone="+5491100000061")
    for i in range(5):
        await client.post("/fields/", json={
            "name": f"Field{i}", "latitude": -31.0 + i, "longitude": -64.0,
            "user_id": str(user_id)
        })

    resp = await client.get(f"/fields/user/{user_id}?skip=0&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get(f"/fields/user/{user_id}?skip=4&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_fields_by_user_not_found(client):
    resp = await client.get(f"/fields/user/{FAKE_ID}")
    assert resp.status_code == 404


# ─── WEATHER ───

async def test_create_weather_data(client):
    field_id = await create_field(client, phone="+5491100000070")
    resp = await client.post("/weather/", json={
        "field_id": str(field_id),
        "event_type": "frost",
        "probability": 85.0,
        "target_date": "2025-01-15"
    })
    assert resp.status_code == 201
    assert resp.json()["probability"] == 85.0


async def test_create_weather_field_not_found(client):
    resp = await client.post("/weather/", json={
        "field_id": FAKE_ID,
        "event_type": "frost",
        "probability": 85.0,
        "target_date": "2025-01-15"
    })
    assert resp.status_code == 404


async def test_get_weather_by_field(client):
    field_id = await create_field(client, phone="+5491100000080")
    await client.post("/weather/", json={
        "field_id": str(field_id),
        "event_type": "hail",
        "probability": 60.0,
        "target_date": "2025-01-15"
    })
    resp = await client.get(f"/weather/field/{field_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_weather_by_field_pagination(client):
    field_id = await create_field(client, phone="+5491100000081")
    for i in range(5):
        await client.post("/weather/", json={
            "field_id": str(field_id),
            "event_type": "frost",
            "probability": 50.0 + i,
            "target_date": f"2025-01-{15 + i}"
        })

    resp = await client.get(f"/weather/field/{field_id}?skip=0&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp = await client.get(f"/weather/field/{field_id}?skip=3&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_weather_by_field_not_found(client):
    resp = await client.get(f"/weather/field/{FAKE_ID}")
    assert resp.status_code == 404


# ─── ALERTS ───

async def test_create_alert(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000090")
    resp = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "frost",
        "threshold": 80.0
    })
    assert resp.status_code == 201
    assert resp.json()["event_type"] == "frost"


async def test_create_alert_user_not_found(client):
    field_id = await create_field(client, phone="+5491100000100")
    resp = await client.post("/alerts/", json={
        "user_id": FAKE_ID,
        "field_id": str(field_id),
        "event_type": "frost",
        "threshold": 80.0
    })
    assert resp.status_code == 404


async def test_create_alert_field_not_found(client):
    user_id = await create_user(client, phone="+5491100000110")
    resp = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": FAKE_ID,
        "event_type": "frost",
        "threshold": 80.0
    })
    assert resp.status_code == 404


async def test_get_user_alerts(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000120")
    await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "hail",
        "threshold": 50.0
    })
    resp = await client.get(f"/alerts/user/{user_id}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_get_user_alerts_pagination(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000121")
    for i in range(5):
        await client.post("/alerts/", json={
            "user_id": str(user_id),
            "field_id": str(field_id),
            "event_type": f"event_{i}",
            "threshold": 50.0 + i
        })

    resp = await client.get(f"/alerts/user/{user_id}?skip=0&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get(f"/alerts/user/{user_id}?skip=4&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_user_alerts_user_not_found(client):
    resp = await client.get(f"/alerts/user/{FAKE_ID}")
    assert resp.status_code == 404


async def test_get_alert_by_id(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000130")
    create = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "drought",
        "threshold": 70.0
    })
    alert_id = create.json()["id"]
    resp = await client.get(f"/alerts/{alert_id}")
    assert resp.status_code == 200


async def test_get_alert_not_found(client):
    resp = await client.get(f"/alerts/{FAKE_ID}")
    assert resp.status_code == 404


async def test_update_alert(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000140")
    create = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "frost",
        "threshold": 80.0
    })
    alert_id = create.json()["id"]
    resp = await client.patch(f"/alerts/{alert_id}", json={"threshold": 50.0})
    assert resp.status_code == 200
    assert resp.json()["threshold"] == 50.0


async def test_update_alert_not_found(client):
    resp = await client.patch(f"/alerts/{FAKE_ID}", json={"threshold": 50.0})
    assert resp.status_code == 404


async def test_delete_alert(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000150")
    create = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "flood",
        "threshold": 60.0
    })
    alert_id = create.json()["id"]
    resp = await client.delete(f"/alerts/{alert_id}")
    assert resp.status_code == 204


async def test_delete_alert_not_found(client):
    resp = await client.delete(f"/alerts/{FAKE_ID}")
    assert resp.status_code == 404


# ─── NOTIFICATIONS ───

async def test_get_notifications_empty(client):
    user_id = await create_user(client, phone="+5491100000160")
    resp = await client.get(f"/notifications/user/{user_id}")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_notifications_user_not_found(client):
    resp = await client.get(f"/notifications/user/{FAKE_ID}")
    assert resp.status_code == 404


async def test_get_notifications_pagination(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000161")

    # Crear una alert real para satisfacer la FK
    alert_resp = await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "frost",
        "threshold": 50.0,
    })
    alert_id = alert_resp.json()["id"]

    # Crear notificaciones con alert_id real
    from app.repositories.notification_repo import NotificationRepository
    async with async_session_factory() as sess:
        repo = NotificationRepository(sess)
        for i in range(5):
            await repo.create(
                user_id=user_id,
                alert_id=alert_id,
                message=f"Notificación {i}",
            )

    resp = await client.get(f"/notifications/user/{user_id}?skip=0&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get(f"/notifications/user/{user_id}?skip=4&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_notification_mark_as_read_not_found(client):
    resp = await client.patch(f"/notifications/{FAKE_ID}/read")
    assert resp.status_code == 404


async def test_notification_mark_as_read(client):
    user_id, field_id = await create_alert_data(client, phone="+5491100000170")
    await client.post("/alerts/", json={
        "user_id": str(user_id),
        "field_id": str(field_id),
        "event_type": "frost",
        "threshold": 30.0
    })
    await client.post("/weather/", json={
        "field_id": str(field_id),
        "event_type": "frost",
        "probability": 85.0,
        "target_date": "2025-01-15"
    })
    resp = await client.get(f"/notifications/user/{user_id}")
    assert resp.status_code == 200