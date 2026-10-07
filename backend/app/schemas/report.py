from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ReportCreate(BaseModel):
    station_id: int
    report_type: str # incorrect_price, fuel_unavailable, incorrect_location, station_closed, incorrect_pressure, charger_unavailable, other
    description: Optional[str] = None

class ReportOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    station_id: int
    station_name: Optional[str] = None
    report_type: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    status: str # pending, reviewed, resolved
