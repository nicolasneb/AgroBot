import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.field_repo import FieldRepository
from app.repositories.user_repo import UserRepository
from app.services.alert_service import AlertService
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(data: AlertCreate, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    field_repo = FieldRepository(session)
    field = await field_repo.get_by_id(data.field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Campo no encontrado")

    service = AlertService(session)
    return await service.create_alert(data)


@router.get("/user/{user_id}", response_model=list[AlertResponse])
async def get_user_alerts(
    user_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    service = AlertService(session)
    return await service.get_user_alerts(user_id, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = AlertService(session)
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID, data: AlertUpdate,
    session: AsyncSession = Depends(get_session),
):
    service = AlertService(session)
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return await service.update_alert(alert_id, data)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = AlertService(session)
    deleted = await service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")