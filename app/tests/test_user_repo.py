from app.repositories.user_repo import UserRepository


async def test_create_user(session):
    repo = UserRepository(session)
    user = await repo.create(name="Test User", phone="+5491100000000")

    assert user.id is not None
    assert user.name == "Test User"
    assert user.phone == "+5491100000000"


async def test_get_user_by_id(session):
    repo = UserRepository(session)
    user = await repo.create(name="Test User", phone="+5491100000001")

    found = await repo.get_by_id(user.id)
    assert found is not None
    assert found.id == user.id


async def test_get_all_users(session):
    repo = UserRepository(session)
    await repo.create(name="User 1", phone="+5491100000002")
    await repo.create(name="User 2", phone="+5491100000003")

    users = await repo.get_all()
    assert len(users) == 2