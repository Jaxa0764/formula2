from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Notification, User
from app.websocket.connection_manager import manager
from app.routers.deps import require_auth, require_admin

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def get_user_notifications(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Retrieve notifications for logged in user."""
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(30).all()

@router.post("/broadcast")
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "announcement",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin broadcasts notification to users and web clients."""
    users = db.query(User).all()
    now = datetime.utcnow()
    
    for u in users:
        notif = Notification(
            user_id=u.id,
            title=title,
            message=message,
            notification_type=notification_type,
            created_at=now
        )
        db.add(notif)
    db.commit()

    await manager.broadcast({
        "type": "ANNOUNCEMENT",
        "title": title,
        "message": message,
        "created_at": now.isoformat()
    })

    return {"message": f"{len(users)} ta foydalanuvchiga xabar jo'natildi"}
