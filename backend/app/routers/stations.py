from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Station, User
from app.schemas.station import StationOut, StationCreate, StationUpdate, BestOptionResponse
from app.services.station_service import get_filtered_stations, enrich_station_data
from app.services.recommendation_service import calculate_best_option
from app.services.audit_service import record_audit
from app.services.alert_service import check_station_offline_alert
from app.websocket.connection_manager import manager
from app.routers.deps import require_admin, get_current_user

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("", response_model=List[StationOut])
def list_stations(
    search: Optional[str] = None,
    city: Optional[str] = None,
    fuel_code: Optional[str] = None,
    only_cng: bool = False,
    only_lpg: bool = False,
    only_ev: bool = False,
    only_gasoline: bool = False,
    only_diesel: bool = False,
    only_open: bool = False,
    only_24_7: bool = False,
    min_cng_pressure: Optional[float] = None,
    user_lat: Optional[float] = Query(None, description="Current user latitude for distance"),
    user_lon: Optional[float] = Query(None, description="Current user longitude for distance"),
    sort_by: Optional[str] = Query("nearest", description="nearest, cheapest, rating, queue, cng_pressure"),
    db: Session = Depends(get_db)
):
    """Retrieve list of fuel & EV stations with dynamic distance calculation and filters."""
    stations = get_filtered_stations(
        db=db,
        search=search,
        city=city,
        fuel_code=fuel_code,
        only_cng=only_cng,
        only_lpg=only_lpg,
        only_ev=only_ev,
        only_gasoline=only_gasoline,
        only_diesel=only_diesel,
        only_open=only_open,
        only_24_7=only_24_7,
        min_cng_pressure=min_cng_pressure,
        user_lat=user_lat,
        user_lon=user_lon,
        sort_by=sort_by
    )
    return stations

@router.get("/recommend/best", response_model=BestOptionResponse)
def get_best_recommendation(
    fuel_code: str = Query("cng", description="cng, lpg, ai_92, ai_95, ev, diesel"),
    user_lat: float = Query(41.311081),
    user_lon: float = Query(69.240562),
    lang: str = Query("uz"),
    db: Session = Depends(get_db)
):
    """Calculate and return the Best Option station considering price, distance, pressure, and queue."""
    best = calculate_best_option(
        db=db,
        fuel_code=fuel_code,
        user_lat=user_lat,
        user_lon=user_lon,
        lang=lang
    )
    if not best:
        raise HTTPException(status_code=404, detail="Mos keluvchi shoxobcha topilmadi")
    return best

@router.get("/{station_id}", response_model=StationOut)
def get_station_detail(
    station_id: int,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")
    return enrich_station_data(station, user_lat, user_lon)

@router.post("", response_model=StationOut)
async def create_station(
    payload: StationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    station = Station(
        name=payload.name,
        brand=payload.brand,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        city=payload.city or "Tashkent",
        phone=payload.phone,
        working_hours=payload.working_hours or "24/7",
        is_open=payload.is_open,
        is_24_7=payload.is_24_7,
        queue_length=payload.queue_length or 0,
        queue_wait_minutes=payload.queue_wait_minutes or 0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        updated_by=current_user.name
    )
    db.add(station)
    db.commit()
    db.refresh(station)

    # Audit log
    record_audit(
        db=db,
        action="CREATE_STATION",
        entity="station",
        entity_id=station.id,
        new_values=payload.model_dump(),
        user=current_user
    )

    enriched = enrich_station_data(station)
    await manager.broadcast({
        "type": "STATION_CREATED",
        "station": enriched
    })

    return enriched

@router.put("/{station_id}", response_model=StationOut)
async def update_station(
    station_id: int,
    payload: StationUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    old_data = {
        "name": station.name,
        "is_open": station.is_open,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "queue_length": station.queue_length
    }

    update_fields = payload.model_dump(exclude_unset=True)
    for field, val in update_fields.items():
        setattr(station, field, val)
        
    station.updated_at = datetime.utcnow()
    station.updated_by = current_user.name
    db.commit()
    db.refresh(station)

    record_audit(
        db=db,
        action="UPDATE_STATION",
        entity="station",
        entity_id=station.id,
        old_values=old_data,
        new_values=update_fields,
        user=current_user
    )

    if "is_open" in update_fields:
        check_station_offline_alert(db, station.id, station.is_open, station.name)

    enriched = enrich_station_data(station)
    await manager.broadcast({
        "type": "STATION_UPDATED",
        "station": enriched
    })

    return enriched

@router.delete("/{station_id}")
async def delete_station(
    station_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    station_name = station.name
    db.delete(station)
    db.commit()

    record_audit(
        db=db,
        action="DELETE_STATION",
        entity="station",
        entity_id=station_id,
        old_values={"name": station_name},
        user=current_user
    )

    await manager.broadcast({
        "type": "STATION_DELETED",
        "station_id": station_id
    })

    return {"message": "Zapravka muvaffaqiyatli o'chirildi", "station_id": station_id}
