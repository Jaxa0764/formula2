from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.utils.geo import haversine_distance_km, estimate_travel_time_minutes, generate_interpolated_route

router = APIRouter(prefix="/routes", tags=["Routing"])

@router.get("")
def calculate_route(
    start_lat: float = Query(..., description="User latitude"),
    start_lon: float = Query(..., description="User longitude"),
    end_lat: float = Query(..., description="Station latitude"),
    end_lon: float = Query(..., description="Station longitude")
):
    """Calculate driving route geometry, distance, and duration to a station."""
    distance_km = haversine_distance_km(start_lat, start_lon, end_lat, end_lon)
    duration_mins = estimate_travel_time_minutes(distance_km)
    waypoints = generate_interpolated_route(start_lat, start_lon, end_lat, end_lon, steps=12)

    return {
        "distance_km": distance_km,
        "duration_minutes": duration_mins,
        "coordinates": waypoints,
        "steps": [
            {"instruction": "Joriy joylashuvdan yo'lga chiqing", "distance": f"{round(distance_km * 0.2, 1)} km"},
            {"instruction": "Asosiy magistral bo'ylab harakatlaning", "distance": f"{round(distance_km * 0.6, 1)} km"},
            {"instruction": "Shoxobchaga o'ng tomonga buriling", "distance": f"{round(distance_km * 0.2, 1)} km"}
        ]
    }
