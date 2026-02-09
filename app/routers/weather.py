import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.field_repo import FieldRepository
from app.repositories.weather_repo import WeatherRepository
from app.schemas.weather_data import WeatherDataCreate, WeatherDataResponse

router = APIRouter(prefix="/weather", tags=["Weather Data"])


@router.post("/", response_model=WeatherDataResponse, status_code=201)
async def create_weather_data(
    data: WeatherDataCreate, session: AsyncSession = Depends(get_session),
):
    field_repo = FieldRepository(session)
    field = await field_repo.get_by_id(data.field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Campo no encontrado")

    repo = WeatherRepository(session)
    return await repo.create(
        field_id=data.field_id, event_type=data.event_type,
        probability=data.probability, target_date=data.target_date,
    )


@router.get("/field/{field_id}", response_model=list[WeatherDataResponse])
async def get_field_weather(
    field_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    field_repo = FieldRepository(session)
    field = await field_repo.get_by_id(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Campo no encontrado")

    repo = WeatherRepository(session)
    return await repo.get_by_field(field_id, skip=skip, limit=limit)