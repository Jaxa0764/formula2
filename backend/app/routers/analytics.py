from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Station, StationFuel, FuelType, CNGData, LPGData, EVCharger, PriceHistory

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview-summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Summary metrics across all fuel types and EV chargers."""
    fuel_stats = []
    fuel_types = db.query(FuelType).filter(FuelType.is_active == True).all()

    for ft in fuel_types:
        avg_p = db.query(func.avg(StationFuel.price)).filter(
            StationFuel.fuel_type_id == ft.id,
            StationFuel.is_available == True
        ).scalar()
        min_p = db.query(func.min(StationFuel.price)).filter(
            StationFuel.fuel_type_id == ft.id,
            StationFuel.is_available == True
        ).scalar()
        max_p = db.query(func.max(StationFuel.price)).filter(
            StationFuel.fuel_type_id == ft.id,
            StationFuel.is_available == True
        ).scalar()

        if avg_p:
            fuel_stats.append({
                "code": ft.code,
                "name": ft.name,
                "category": ft.category,
                "average_price": round(float(avg_p), 0),
                "min_price": round(float(min_p), 0),
                "max_price": round(float(max_p), 0)
            })

    # CNG stats
    avg_cng = db.query(func.avg(CNGData.price)).filter(CNGData.is_available == True).scalar() or 3750.0
    avg_cng_pres = db.query(func.avg(CNGData.pressure_bar)).filter(CNGData.is_available == True).scalar() or 195.0

    # EV stats
    avg_ev = db.query(func.avg(EVCharger.price_per_kwh)).scalar() or 2400.0
    total_chargers = db.query(func.sum(EVCharger.total_chargers)).scalar() or 0
    avail_chargers = db.query(func.sum(EVCharger.available_chargers)).scalar() or 0

    return {
        "fuels": fuel_stats,
        "cng": {
            "average_price": round(float(avg_cng), 0),
            "average_pressure_bar": round(float(avg_cng_pres), 1)
        },
        "ev": {
            "average_price_per_kwh": round(float(avg_ev), 0),
            "total_ports": int(total_chargers),
            "available_ports": int(avail_chargers)
        }
    }

@router.get("/price-trends")
def get_price_trends(
    period: str = Query("30d", description="24h, 7d, 30d, 90d"),
    db: Session = Depends(get_db)
):
    """Historical price trends for charts."""
    days = 30
    if period == "24h":
        days = 1
    elif period == "7d":
        days = 7
    elif period == "90d":
        days = 90

    cutoff = datetime.utcnow() - timedelta(days=days)
    records = db.query(PriceHistory).filter(PriceHistory.recorded_at >= cutoff).order_by(PriceHistory.recorded_at.asc()).all()

    # Group by date and fuel type
    trend_map: Dict[str, Dict[str, List[float]]] = {}
    for r in records:
        date_str = r.recorded_at.strftime("%Y-%m-%d" if days > 1 else "%H:%M")
        fuel_name = r.fuel_type.name if r.fuel_type else "Yoqilg'i"
        if date_str not in trend_map:
            trend_map[date_str] = {}
        if fuel_name not in trend_map[date_str]:
            trend_map[date_str][fuel_name] = []
        trend_map[date_str][fuel_name].append(r.price)

    labels = sorted(list(trend_map.keys()))
    datasets = []
    
    # Representative fuel lines
    fuel_colors = {
        "AI-92": "#00F2FE",
        "AI-95": "#4FACFE",
        "AI-80": "#94A3B8",
        "Dizel": "#F59E0B",
        "Methane (CNG)": "#10B981",
        "Propane (LPG)": "#EC4899"
    }

    all_fuels = set()
    for d in trend_map.values():
        all_fuels.update(d.keys())

    for fuel in sorted(list(all_fuels)):
        data_points = []
        for l in labels:
            if fuel in trend_map[l]:
                avg_val = sum(trend_map[l][fuel]) / len(trend_map[l][fuel])
                data_points.append(round(avg_val, 0))
            else:
                data_points.append(None)
        datasets.append({
            "label": fuel,
            "data": data_points,
            "borderColor": fuel_colors.get(fuel, "#3B82F6"),
            "backgroundColor": "transparent",
            "tension": 0.3
        })

    return {
        "labels": labels,
        "datasets": datasets
    }
