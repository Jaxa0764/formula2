import math
from typing import List, Tuple, Dict, Any

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0 # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_travel_time_minutes(distance_km: float) -> int:
    """Estimate driving travel time in minutes assuming average city traffic (35 km/h) plus stoplight delay."""
    if distance_km <= 0.05:
        return 1
    # Average speed in Uzbek cities ~ 35 km/h + 2 min base traffic
    hours = distance_km / 35.0
    minutes = int(math.ceil(hours * 60)) + 2
    return max(1, minutes)

def generate_interpolated_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, steps: int = 8) -> List[List[float]]:
    """Generate realistic intermediate route coordinates for visualization on map."""
    route = []
    # Add a slight realistic curve to simulate road curves rather than direct straight line
    mid_lat = (start_lat + end_lat) / 2
    mid_lon = (start_lon + end_lon) / 2
    
    # Slight orthogonal jitter to look like city street grid
    dx = end_lon - start_lon
    dy = end_lat - start_lat
    perp_lat = -dx * 0.12
    perp_lon = dy * 0.12
    
    control_lat = mid_lat + perp_lat
    control_lon = mid_lon + perp_lon
    
    # Quadratic Bezier
    for i in range(steps + 1):
        t = i / steps
        lat = (1 - t)**2 * start_lat + 2 * (1 - t) * t * control_lat + t**2 * end_lat
        lon = (1 - t)**2 * start_lon + 2 * (1 - t) * t * control_lon + t**2 * end_lon
        route.append([round(lat, 6), round(lon, 6)])
        
    return route
