from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import StationFuel, PriceHistory, Station, FuelType, User
from app.schemas.admin import BulkPriceUpdate
from app.services.audit_service import record_audit
from app.websocket.connection_manager import manager
from app.routers.deps import require_admin

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.post("/bulk-update")
async def bulk_update_prices(
    payload: BulkPriceUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin updates fuel prices across stations in bulk."""
    fuel_type = db.query(FuelType).filter(FuelType.id == payload.fuel_type_id).first()
    if not fuel_type:
        raise HTTPException(status_code=404, detail="Yoqilg'i turi topilmadi")

    query = db.query(StationFuel).filter(StationFuel.fuel_type_id == payload.fuel_type_id)
    if payload.station_ids:
        query = query.filter(StationFuel.station_id.in_(payload.station_ids))
    
    fuels = query.all()
    count = 0
    now = datetime.utcnow()

    for f in fuels:
        old_price = f.price
        f.price = payload.price
        f.last_updated = now
        f.updated_by = current_user.name

        # Record history
        history = PriceHistory(
            station_id=f.station_id,
            fuel_type_id=f.fuel_type_id,
            price=payload.price,
            recorded_at=now
        )
        db.add(history)
        count += 1

    db.commit()

    record_audit(
        db=db,
        action="BULK_PRICE_UPDATE",
        entity="station_fuels",
        new_values={"fuel": fuel_type.name, "new_price": payload.price, "stations_count": count},
        user=current_user
    )

    await manager.broadcast({
        "type": "PRICE_UPDATED",
        "data": {
            "fuel_code": fuel_type.code,
            "fuel_name": fuel_type.name,
            "new_price": payload.price,
            "updated_at": now.isoformat()
        }
    })

    return {"message": f"{count} ta shoxobchada {fuel_type.name} narxi {payload.price} so'mga yangilandi", "count": count}

@router.post("/station/{station_id}")
async def update_station_fuel_price(
    station_id: int,
    fuel_type_id: int,
    price: float,
    is_available: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update price and availability for specific station fuel."""
    fuel = db.query(StationFuel).filter(
        StationFuel.station_id == station_id,
        StationFuel.fuel_type_id == fuel_type_id
    ).first()

    now = datetime.utcnow()
    old_price = fuel.price if fuel else None

    if fuel:
        fuel.price = price
        fuel.is_available = is_available
        fuel.last_updated = now
        fuel.updated_by = current_user.name
    else:
        fuel = StationFuel(
            station_id=station_id,
            fuel_type_id=fuel_type_id,
            price=price,
            is_available=is_available,
            last_updated=now,
            updated_by=current_user.name
        )
        db.add(fuel)

    # Save to history
    history = PriceHistory(
        station_id=station_id,
        fuel_type_id=fuel_type_id,
        price=price,
        recorded_at=now
    )
    db.add(history)
    db.commit()

    record_audit(
        db=db,
        action="UPDATE_STATION_FUEL_PRICE",
        entity="station_fuels",
        entity_id=station_id,
        old_values={"price": old_price},
        new_values={"price": price, "is_available": is_available},
        user=current_user
    )

    await manager.broadcast({
        "type": "STATION_FUEL_UPDATED",
        "station_id": station_id,
        "fuel_type_id": fuel_type_id,
        "price": price,
        "is_available": is_available,
        "updated_at": now.isoformat()
    })

    return {"message": "Yoqilg'i narxi yangilandi", "price": price}

@router.get("/history/{station_id}")
def get_price_history(
    station_id: int,
    fuel_type_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieve historical prices for charts."""
    query = db.query(PriceHistory).filter(PriceHistory.station_id == station_id)
    if fuel_type_id:
        query = query.filter(PriceHistory.fuel_type_id == fuel_type_id)
    history = query.order_by(PriceHistory.recorded_at.asc()).limit(100).all()
    
    return [
        {
            "id": h.id,
            "station_id": h.station_id,
            "fuel_type_id": h.fuel_type_id,
            "fuel_name": h.fuel_type.name if h.fuel_type else "",
            "price": h.price,
            "recorded_at": h.recorded_at
        }
        for h in history
    ]
