import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.field_repo import FieldRepository
from app.repositories.user_repo import UserRepository
from app.schemas.field import FieldCreate, FieldResponse

router = APIRouter(prefix="/fields", tags=["Fields"])


@router.post("/", response_model=FieldResponse, status_code=201)
async def create_field(data: FieldCreate, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    repo = FieldRepository(session)
    return await repo.create(
        user_id=data.user_id, name=data.name,
        latitude=data.latitude, longitude=data.longitude,
    )


@router.get("/user/{user_id}", response_model=list[FieldResponse])
async def get_user_fields(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    repo = FieldRepository(session)
    return await repo.get_by_user(user_id, skip=skip, limit=limit)


@router.get("/{field_id}", response_model=FieldResponse)
async def get_field(field_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    repo = FieldRepository(session)
    field = await repo.get_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Campo no encontrado")
    return field