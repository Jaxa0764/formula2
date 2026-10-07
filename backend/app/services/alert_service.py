from typing import Optional
from sqlalchemy.orm import Session
from app.models import SystemAlert, AlertSeverity, Station

def check_and_create_cng_alert(db: Session, station_id: int, pressure_bar: float, station_name: str) -> Optional[SystemAlert]:
    """Check CNG pressure and generate alerts if low."""
    if pressure_bar < 130:
        alert = SystemAlert(
            severity=AlertSeverity.CRITICAL.value,
            title=f"Kritik past metan bosimi: {station_name}",
            message=f"Zapravkada CNG bosimi {pressure_bar} bar gacha pasayib ketdi! Haydovchilarga ogohlantirish berildi.",
            station_id=station_id,
            is_active=True
        )
        db.add(alert)
        db.commit()
        return alert
    elif pressure_bar < 160:
        alert = SystemAlert(
            severity=AlertSeverity.WARNING.value,
            title=f"Past metan bosimi: {station_name}",
            message=f"Zapravkada CNG bosimi {pressure_bar} bar. Navbat sekinlashishi mumkin.",
            station_id=station_id,
            is_active=True
        )
        db.add(alert)
        db.commit()
        return alert
    return None

def check_station_offline_alert(db: Session, station_id: int, is_open: bool, station_name: str) -> Optional[SystemAlert]:
    """Alert when a station becomes offline or closes unexpectedly."""
    if not is_open:
        alert = SystemAlert(
            severity=AlertSeverity.WARNING.value,
            title=f"Zapravka faoliyati to'xtatildi: {station_name}",
            message=f"{station_name} shoxobchasi vaqtincha yopildi yoki oflayn holatga o'tdi.",
            station_id=station_id,
            is_active=True
        )
        db.add(alert)
        db.commit()
        return alert
    return None
