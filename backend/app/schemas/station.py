from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FuelTypeOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    unit: str
    is_active: bool

    class Config:
        from_attributes = True

class StationFuelOut(BaseModel):
    id: int
    station_id: int
    fuel_type_id: int
    fuel_code: Optional[str] = None
    fuel_name: Optional[str] = None
    fuel_unit: Optional[str] = None
    is_available: bool
    price: float
    quantity_status: str
    last_updated: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class StationFuelUpdate(BaseModel):
    fuel_type_id: int
    is_available: bool = True
    price: float
    quantity_status: Optional[str] = "normal"

class CNGDataOut(BaseModel):
    id: int
    station_id: int
    is_available: bool
    pressure_bar: float
    price: float
    status: str
    last_updated: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class CNGDataUpdate(BaseModel):
    is_available: bool = True
    pressure_bar: float
    price: Optional[float] = 3750.0
    status: Optional[str] = "available"

class LPGDataOut(BaseModel):
    id: int
    station_id: int
    is_available: bool
    pressure_bar: float
    price: float
    status: str
    last_updated: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class LPGDataUpdate(BaseModel):
    is_available: bool = True
    pressure_bar: Optional[float] = 12.0
    price: float
    status: Optional[str] = "available"

class EVChargerOut(BaseModel):
    id: int
    station_id: int
    charger_type: str
    connector_type: str
    total_chargers: int
    available_chargers: int
    power_kw: float
    price_per_kwh: float
    status: str
    last_updated: datetime
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class EVChargerUpdate(BaseModel):
    charger_type: str
    connector_type: str
    total_chargers: int
    available_chargers: int
    power_kw: float
    price_per_kwh: float
    status: str

class ReviewCreate(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    service_rating: Optional[float] = 5.0
    cleanliness_rating: Optional[float] = 5.0
    queue_rating: Optional[float] = 5.0
    fuel_quality_rating: Optional[float] = 5.0
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    station_id: int
    user_id: int
    user_name: Optional[str] = "Foydalanuvchi"
    rating: float
    service_rating: float
    cleanliness_rating: float
    queue_rating: float
    fuel_quality_rating: float
    comment: Optional[str] = None
    moderation_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class StationBase(BaseModel):
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    latitude: float
    longitude: float
    address: str
    city: Optional[str] = "Tashkent"
    phone: Optional[str] = None
    working_hours: Optional[str] = "24/7"
    is_open: bool = True
    is_24_7: bool = True
    queue_length: Optional[int] = 0
    queue_wait_minutes: Optional[int] = 0

class StationCreate(StationBase):
    pass

class StationUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    working_hours: Optional[str] = None
    is_open: Optional[bool] = None
    is_24_7: Optional[bool] = None
    queue_length: Optional[int] = None
    queue_wait_minutes: Optional[int] = None

class StationOut(StationBase):
    id: int
    rating: float
    reviews_count: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None
    
    # Nested data
    fuels: List[StationFuelOut] = []
    cng_data: Optional[CNGDataOut] = None
    lpg_data: Optional[LPGDataOut] = None
    chargers: List[EVChargerOut] = []
    
    # Dynamic computed fields
    distance_km: Optional[float] = None
    estimated_time_mins: Optional[int] = None
    has_cng: Optional[bool] = False
    has_lpg: Optional[bool] = False
    has_ev: Optional[bool] = False
    has_fuel: Optional[bool] = False
    best_option_score: Optional[float] = None
    best_option_reason: Optional[str] = None

    class Config:
        from_attributes = True

class BestOptionResponse(BaseModel):
    station: StationOut
    score: float
    reasons: List[str]
    fuel_code: str
    calculated_at: datetime
