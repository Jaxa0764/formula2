from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import (
    Station, User, StationFuel, CNGData, LPGData, EVCharger, Report, AuditLog, SystemAlert
)
from app.schemas.admin import AdminOverviewStats, AuditLogOut, AlertOut
from app.schemas.auth import UserOut
from app.routers.deps import require_admin

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

@router.get("/overview", response_model=AdminOverviewStats)
def get_admin_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve top-level KPI metrics for administrator dashboard."""
    total_st = db.query(Station).count()
    active_st = db.query(Station).filter(Station.is_open == True).count()
    cng_avail = db.query(CNGData).filter(CNGData.is_available == True).count()
    lpg_avail = db.query(LPGData).filter(LPGData.is_available == True).count()
    fuel_avail = db.query(StationFuel).filter(StationFuel.is_available == True).distinct(StationFuel.station_id).count()
    ev_chargers_count = db.query(EVCharger).filter(EVCharger.status != "offline").count()
    low_pres = db.query(CNGData).filter(CNGData.pressure_bar < 140, CNGData.is_available == True).count()
    offline_st = db.query(Station).filter(Station.is_open == False).count()
    pending_rep = db.query(Report).filter(Report.status == "pending").count()
    user_cnt = db.query(User).count()
    
    avg_pres = db.query(func.avg(CNGData.pressure_bar)).filter(CNGData.is_available == True).scalar() or 0.0

    # Minimum prices
    min_ai92 = db.query(func.min(StationFuel.price)).join(StationFuel.fuel_type).filter(
        StationFuel.fuel_type.has(code="ai_92"),
        StationFuel.is_available == True
    ).scalar()

    min_cng = db.query(func.min(CNGData.price)).filter(CNGData.is_available == True).scalar()

    return {
        "total_stations": total_st,
        "active_stations": active_st,
        "cng_available": cng_avail,
        "lpg_available": lpg_avail,
        "fuel_available": fuel_avail,
        "ev_chargers": ev_chargers_count,
        "low_pressure_stations": low_pres,
        "offline_stations": offline_st,
        "pending_reports": pending_rep,
        "user_count": user_cnt,
        "avg_cng_pressure": round(float(avg_pres), 1),
        "cheapest_ai92_price": min_ai92,
        "cheapest_cng_price": min_cng
    }

@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve administrative audit trail."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

@router.get("/alerts", response_model=List[AlertOut])
def get_alerts(
    only_active: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retrieve system alerts (pressure drops, station down, report surges)."""
    query = db.query(SystemAlert)
    if only_active:
        query = query.filter(SystemAlert.is_active == True)
    alerts = query.order_by(SystemAlert.created_at.desc()).limit(50).all()

    out = []
    for a in alerts:
        st_name = None
        if a.station_id:
            st = db.query(Station).filter(Station.id == a.station_id).first()
            if st:
                st_name = st.name
        out.append({
            "id": a.id,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "station_id": a.station_id,
            "station_name": st_name,
            "is_active": a.is_active,
            "created_at": a.created_at
        })
    return out

@router.post("/alerts/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Ogohlantirish topilmadi")
    alert.is_active = False
    db.commit()
    return {"message": "Ogohlantirish o'chirildi"}

@router.get("/users", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List system users for administration."""
    return db.query(User).order_by(User.created_at.desc()).all()

@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    role: str, # user, station_manager, moderator, admin, super_admin
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    target.role = role
    db.commit()
    return {"message": f"Foydalanuvchi roli {role} ga o'zgartirildi"}
