from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EVCharger, Station, User
from app.schemas.station import EVChargerOut, EVChargerUpdate
from app.services.audit_service import record_audit
from app.websocket.connection_manager import manager
from app.routers.deps import require_admin

router = APIRouter(prefix="/chargers", tags=["EV Chargers"])

@router.get("/station/{station_id}", response_model=List[EVChargerOut])
def get_station_chargers(station_id: int, db: Session = Depends(get_db)):
    return db.query(EVCharger).filter(EVCharger.station_id == station_id).all()

@router.post("/station/{station_id}", response_model=EVChargerOut)
async def add_station_charger(
    station_id: int,
    payload: EVChargerUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    charger = EVCharger(
        station_id=station_id,
        charger_type=payload.charger_type,
        connector_type=payload.connector_type,
        total_chargers=payload.total_chargers,
        available_chargers=payload.available_chargers,
        power_kw=payload.power_kw,
        price_per_kwh=payload.price_per_kwh,
        status=payload.status,
        last_updated=datetime.utcnow(),
        updated_by=current_user.name
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)

    await manager.broadcast({
        "type": "EV_CHARGER_UPDATED",
        "station_id": station_id,
        "charger_id": charger.id,
        "available_chargers": charger.available_chargers,
        "status": charger.status
    })

    return charger

@router.put("/{charger_id}", response_model=EVChargerOut)
async def update_charger(
    charger_id: int,
    payload: EVChargerUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    charger = db.query(EVCharger).filter(EVCharger.id == charger_id).first()
    if not charger:
        raise HTTPException(status_code=404, detail="EV zaryadlagich topilmadi")

    charger.charger_type = payload.charger_type
    charger.connector_type = payload.connector_type
    charger.total_chargers = payload.total_chargers
    charger.available_chargers = payload.available_chargers
    charger.power_kw = payload.power_kw
    charger.price_per_kwh = payload.price_per_kwh
    charger.status = payload.status
    charger.last_updated = datetime.utcnow()
    charger.updated_by = current_user.name

    db.commit()
    db.refresh(charger)

    record_audit(
        db=db,
        action="UPDATE_EV_CHARGER",
        entity="ev_chargers",
        entity_id=charger_id,
        new_values=payload.model_dump(),
        user=current_user
    )

    await manager.broadcast({
        "type": "EV_CHARGER_UPDATED",
        "station_id": charger.station_id,
        "charger_id": charger.id,
        "available_chargers": charger.available_chargers,
        "status": charger.status,
        "price_per_kwh": charger.price_per_kwh
    })

    return charger
