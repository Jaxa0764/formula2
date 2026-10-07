from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report, Station, User
from app.schemas.report import ReportCreate, ReportOut, ReportUpdate
from app.routers.deps import require_admin, get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("", response_model=ReportOut)
def create_report(
    payload: ReportCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User reports incorrect data or problem at a station."""
    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    report = Report(
        user_id=current_user.id if current_user else None,
        station_id=payload.station_id,
        report_type=payload.report_type,
        description=payload.description,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "id": report.id,
        "user_id": report.user_id,
        "user_email": current_user.email if current_user else "Anonim",
        "station_id": report.station_id,
        "station_name": station.name,
        "report_type": report.report_type,
        "description": report.description,
        "status": report.status,
        "created_at": report.created_at
    }

@router.get("", response_model=List[ReportOut])
def list_reports(
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin reviews problem reports."""
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    reports = query.order_by(Report.created_at.desc()).all()

    out = []
    for r in reports:
        out.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_email": r.user.email if r.user else "Anonim",
            "station_id": r.station_id,
            "station_name": r.station.name if r.station else "Noma'lum",
            "report_type": r.report_type,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at
        })
    return out

@router.put("/{report_id}/status")
def update_report_status(
    report_id: int,
    payload: ReportUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Hisobot topilmadi")
    report.status = payload.status
    db.commit()
    return {"message": "Hisobot holati yangilandi", "status": payload.status}
