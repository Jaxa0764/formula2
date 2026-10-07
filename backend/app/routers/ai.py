from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import process_ai_query

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.post("/chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, db: Session = Depends(get_db)):
    """
    AI Assistant endpoint providing intelligent answers, comparisons, 
    and recommendations grounded in real database records.
    """
    user_lat = payload.user_location.get("latitude", 41.311081) if payload.user_location else 41.311081
    user_lon = payload.user_location.get("longitude", 69.240562) if payload.user_location else 69.240562
    lang = payload.lang or "uz"

    result = process_ai_query(
        db=db,
        query=payload.message,
        user_lat=user_lat,
        user_lon=user_lon,
        lang=lang
    )

    return result
