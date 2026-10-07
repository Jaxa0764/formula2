from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AdminOverviewStats(BaseModel):
    total_stations: int
    active_stations: int
    cng_available: int
    lpg_available: int
    fuel_available: int
    ev_chargers: int
    low_pressure_stations: int
    offline_stations: int
    pending_reports: int
    user_count: int
    avg_cng_pressure: float
    cheapest_ai92_price: Optional[float] = None
    cheapest_cng_price: Optional[float] = None

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: str
    action: str
    entity: str
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    severity: str
    title: str
    message: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class BulkPriceUpdate(BaseModel):
    fuel_type_id: int
    price: float
    station_ids: Optional[List[int]] = None # None means all stations
