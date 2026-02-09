from app.repositories.user_repo import UserRepository
from app.repositories.field_repo import FieldRepository


async def test_create_field(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000010")

    field_repo = FieldRepository(session)
    field = await field_repo.create(
        user_id=user.id, name="Campo Test",
        latitude=-34.60, longitude=-58.38,
    )

    assert field.id is not None
    assert field.name == "Campo Test"
    assert field.user_id == user.id


async def test_get_fields_by_user(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(name="Test User", phone="+5491100000011")

    field_repo = FieldRepository(session)
    await field_repo.create(user_id=user.id, name="Campo 1", latitude=-34.0, longitude=-58.0)
    await field_repo.create(user_id=user.id, name="Campo 2", latitude=-33.0, longitude=-60.0)

    fields = await field_repo.get_by_user(user.id)
    assert len(fields) == 2