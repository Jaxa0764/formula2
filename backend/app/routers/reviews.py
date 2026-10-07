from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Review, Station, User, ModerationStatus
from app.schemas.station import ReviewOut, ReviewCreate
from app.routers.deps import require_auth, require_moderator

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("/station/{station_id}", response_model=List[ReviewOut])
def get_station_reviews(station_id: int, db: Session = Depends(get_db)):
    """Retrieve approved reviews for a station."""
    reviews = db.query(Review).filter(
        Review.station_id == station_id,
        Review.moderation_status == ModerationStatus.APPROVED.value
    ).order_by(Review.created_at.desc()).all()
    
    out = []
    for r in reviews:
        out.append({
            "id": r.id,
            "station_id": r.station_id,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else "Foydalanuvchi",
            "rating": r.rating,
            "service_rating": r.service_rating,
            "cleanliness_rating": r.cleanliness_rating,
            "queue_rating": r.queue_rating,
            "fuel_quality_rating": r.fuel_quality_rating,
            "comment": r.comment,
            "moderation_status": r.moderation_status,
            "created_at": r.created_at
        })
    return out

@router.post("/station/{station_id}", response_model=ReviewOut)
def create_review(
    station_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Zapravka topilmadi")

    review = Review(
        station_id=station_id,
        user_id=current_user.id,
        rating=payload.rating,
        service_rating=payload.service_rating or 5.0,
        cleanliness_rating=payload.cleanliness_rating or 5.0,
        queue_rating=payload.queue_rating or 5.0,
        fuel_quality_rating=payload.fuel_quality_rating or 5.0,
        comment=payload.comment,
        moderation_status=ModerationStatus.APPROVED.value, # Auto-approved for fast feedback
        created_at=datetime.utcnow()
    )
    db.add(review)
    db.commit()

    # Recalculate average rating
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.station_id == station_id,
        Review.moderation_status == ModerationStatus.APPROVED.value
    ).scalar() or payload.rating
    count = db.query(Review).filter(
        Review.station_id == station_id,
        Review.moderation_status == ModerationStatus.APPROVED.value
    ).count()

    station.rating = round(float(avg_rating), 1)
    station.reviews_count = count
    db.commit()
    db.refresh(review)

    return {
        "id": review.id,
        "station_id": review.station_id,
        "user_id": review.user_id,
        "user_name": current_user.name,
        "rating": review.rating,
        "service_rating": review.service_rating,
        "cleanliness_rating": review.cleanliness_rating,
        "queue_rating": review.queue_rating,
        "fuel_quality_rating": review.fuel_quality_rating,
        "comment": review.comment,
        "moderation_status": review.moderation_status,
        "created_at": review.created_at
    }

@router.get("/pending", response_model=List[ReviewOut])
def list_pending_reviews(
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    reviews = db.query(Review).filter(Review.moderation_status == ModerationStatus.PENDING.value).all()
    return [
        {
            "id": r.id,
            "station_id": r.station_id,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else "Anonim",
            "rating": r.rating,
            "service_rating": r.service_rating,
            "cleanliness_rating": r.cleanliness_rating,
            "queue_rating": r.queue_rating,
            "fuel_quality_rating": r.fuel_quality_rating,
            "comment": r.comment,
            "moderation_status": r.moderation_status,
            "created_at": r.created_at
        }
        for r in reviews
    ]

@router.put("/{review_id}/moderate")
def moderate_review(
    review_id: int,
    status: str, # approved, rejected
    current_user: User = Depends(require_moderator),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Sharh topilmadi")
    review.moderation_status = status
    db.commit()
    return {"message": f"Sharh holati o'zgartirildi: {status}"}
