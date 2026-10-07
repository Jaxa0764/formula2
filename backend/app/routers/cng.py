from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CNGData, Station, User
from app.schemas.station import CNGDataUpdate, CNGDataOut
from app.services.alert_service import check_and_create_cng_alert
from app.services.audit_service import record_audit
from app.websocket.connection_manager import manager
from app.routers.deps import require_admin

router = APIRouter(prefix="/cng", tags=["CNG Methane"])

@router.put("/update/{station_id}", response_model=CNGDataOut)
async def update_cng_data(
    station_id: int,
    payload: CNGDataUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin updates CNG (Methane) pressure, status, and price."""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    cng = db.query(CNGData).filter(CNGData.station_id == station_id).first()
    now = datetime.utcnow()
    old_pressure = cng.pressure_bar if cng else None

    # Derive status automatically if low pressure
    status_str = payload.status or "available"
    if payload.pressure_bar < 130:
        status_str = "low_pressure"

    if cng:
        cng.is_available = payload.is_available
        cng.pressure_bar = payload.pressure_bar
        cng.price = payload.price or cng.price
        cng.status = status_str
        cng.last_updated = now
        cng.updated_by = current_user.name
    else:
        cng = CNGData(
            station_id=station_id,
            is_available=payload.is_available,
            pressure_bar=payload.pressure_bar,
            price=payload.price or 3750.0,
            status=status_str,
            last_updated=now,
            updated_by=current_user.name
        )
        db.add(cng)

    db.commit()
    db.refresh(cng)

    # Check for alerts
    alert = check_and_create_cng_alert(db, station_id, payload.pressure_bar, station.name)

    # Record audit log
    record_audit(
        db=db,
        action="UPDATE_CNG_PRESSURE",
        entity="cng_data",
        entity_id=station_id,
        old_values={"pressure_bar": old_pressure},
        new_values={"pressure_bar": payload.pressure_bar, "status": status_str, "price": cng.price},
        user=current_user
    )

    # Broadcast WebSocket update
    await manager.broadcast({
        "type": "CNG_PRESSURE_UPDATED",
        "station_id": station_id,
        "station_name": station.name,
        "pressure_bar": cng.pressure_bar,
        "status": cng.status,
        "price": cng.price,
        "is_available": cng.is_available,
        "updated_at": now.isoformat(),
        "alert": alert.title if alert else None
    })

    return cng
