from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Favorite, Station, User
from app.routers.deps import require_auth
from app.services.station_service import enrich_station_data

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get("")
def get_user_favorites(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Retrieve user's favorite stations."""
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    out = []
    for fav in favorites:
        st = db.query(Station).filter(Station.id == fav.station_id).first()
        if st:
            out.append(enrich_station_data(st))
    return out

@router.post("/{station_id}")
def add_favorite(
    station_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save station to favorites."""
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.station_id == station_id
    ).first()
    if existing:
        return {"message": "Allaqachon sevimlilarga qo'shilgan", "station_id": station_id}
    
    fav = Favorite(user_id=current_user.id, station_id=station_id, created_at=datetime.utcnow())
    db.add(fav)
    db.commit()
    return {"message": "Sevimlilarga qo'shildi", "station_id": station_id}

@router.delete("/{station_id}")
def remove_favorite(
    station_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Remove station from favorites."""
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.station_id == station_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"message": "Sevimlilardan o'chirildi", "station_id": station_id}
