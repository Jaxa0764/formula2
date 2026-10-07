from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FuelType, User
from app.schemas.station import FuelTypeOut
from app.routers.deps import require_admin

router = APIRouter(prefix="/fuels", tags=["Fuels"])

@router.get("/types", response_model=List[FuelTypeOut])
def list_fuel_types(db: Session = Depends(get_db)):
    """Retrieve all supported fuel types (extensible by admins)."""
    return db.query(FuelType).filter(FuelType.is_active == True).all()

@router.post("/types", response_model=FuelTypeOut)
def create_fuel_type(
    code: str,
    name: str,
    category: str = "gasoline",
    unit: str = "liter",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Allow administrators to dynamically add new fuel types."""
    existing = db.query(FuelType).filter(FuelType.code == code.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ushbu yoqilg'i turi allaqachon mavjud")
    
    ft = FuelType(
        code=code.lower(),
        name=name,
        category=category,
        unit=unit,
        is_active=True
    )
    db.add(ft)
    db.commit()
    db.refresh(ft)
    return ft
