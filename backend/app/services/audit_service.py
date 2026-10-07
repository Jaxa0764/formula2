from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog, User

def record_audit(
    db: Session,
    action: str,
    entity: str,
    entity_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    user: Optional[User] = None,
    user_email: Optional[str] = None
) -> AuditLog:
    """Record an audit trail event in database."""
    email = user_email or (user.email if user else "system")
    user_id = user.id if user else None
    
    log = AuditLog(
        user_id=user_id,
        user_email=email,
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
