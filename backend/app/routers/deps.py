from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency to retrieve currently authenticated user from Bearer token."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    email = payload.get("email")
    if not email:
        return None
    user = db.query(User).filter(User.email == email).first()
    return user

def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency requiring user to be logged in."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kirish talab etiladi (Authentication required)",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def require_admin(user: User = Depends(require_auth)) -> User:
    """Dependency requiring admin or super_admin role."""
    if user.role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat administratorlar uchun ruxsat berilgan (Admin privileges required)"
        )
    return user

def require_moderator(user: User = Depends(require_auth)) -> User:
    """Dependency requiring moderator, admin or super_admin role."""
    if user.role not in [UserRole.MODERATOR.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator ruxsati talab etiladi"
        )
    return user
