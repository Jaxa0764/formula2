from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LPGData, Station, User
from app.schemas.station import LPGDataUpdate, LPGDataOut
from app.services.audit_service import record_audit
from app.websocket.connection_manager import manager
from app.routers.deps import require_admin

router = APIRouter(prefix="/lpg", tags=["LPG Propane"])

@router.put("/update/{station_id}", response_model=LPGDataOut)
async def update_lpg_data(
    station_id: int,
    payload: LPGDataUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin updates LPG (Propane) pressure, price, and status."""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    lpg = db.query(LPGData).filter(LPGData.station_id == station_id).first()
    now = datetime.utcnow()
    old_pressure = lpg.pressure_bar if lpg else None

    if lpg:
        lpg.is_available = payload.is_available
        lpg.pressure_bar = payload.pressure_bar or lpg.pressure_bar
        lpg.price = payload.price
        lpg.status = payload.status or "available"
        lpg.last_updated = now
        lpg.updated_by = current_user.name
    else:
        lpg = LPGData(
            station_id=station_id,
            is_available=payload.is_available,
            pressure_bar=payload.pressure_bar or 12.0,
            price=payload.price,
            status=payload.status or "available",
            last_updated=now,
            updated_by=current_user.name
        )
        db.add(lpg)

    db.commit()
    db.refresh(lpg)

    record_audit(
        db=db,
        action="UPDATE_LPG_DATA",
        entity="lpg_data",
        entity_id=station_id,
        old_values={"pressure_bar": old_pressure},
        new_values={"price": payload.price, "is_available": payload.is_available},
        user=current_user
    )

    await manager.broadcast({
        "type": "LPG_UPDATED",
        "station_id": station_id,
        "station_name": station.name,
        "price": lpg.price,
        "is_available": lpg.is_available,
        "status": lpg.status,
        "updated_at": now.isoformat()
    })

    return lpg
