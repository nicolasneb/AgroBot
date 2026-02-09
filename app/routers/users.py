import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    try:
        return await repo.create(name=data.name, phone=data.phone)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="El teléfono ya está registrado")


@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    return await repo.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user