from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from app.models import Station, StationFuel, CNGData, LPGData, EVCharger, FuelType
from app.utils.geo import haversine_distance_km, estimate_travel_time_minutes

def enrich_station_data(station: Station, user_lat: Optional[float] = None, user_lon: Optional[float] = None) -> Dict[str, Any]:
    """Convert Station model to enriched dictionary with calculated distances and flags."""
    distance = None
    est_time = None
    if user_lat is not None and user_lon is not None:
        distance = haversine_distance_km(user_lat, user_lon, station.latitude, station.longitude)
        est_time = estimate_travel_time_minutes(distance)
        
    has_cng = station.cng_data is not None and station.cng_data.is_available
    has_lpg = station.lpg_data is not None and station.lpg_data.is_available
    has_ev = len(station.chargers) > 0 and any(c.status != "offline" for c in station.chargers)
    has_fuel = len(station.fuels) > 0 and any(f.is_available for f in station.fuels)

    fuels_list = []
    for f in station.fuels:
        fuels_list.append({
            "id": f.id,
            "station_id": f.station_id,
            "fuel_type_id": f.fuel_type_id,
            "fuel_code": f.fuel_type.code if f.fuel_type else None,
            "fuel_name": f.fuel_type.name if f.fuel_type else None,
            "fuel_unit": f.fuel_type.unit if f.fuel_type else "liter",
            "is_available": f.is_available,
            "price": f.price,
            "quantity_status": f.quantity_status,
            "last_updated": f.last_updated,
            "updated_by": f.updated_by
        })

    cng_out = None
    if station.cng_data:
        cng_out = {
            "id": station.cng_data.id,
            "station_id": station.id,
            "is_available": station.cng_data.is_available,
            "pressure_bar": station.cng_data.pressure_bar,
            "price": station.cng_data.price,
            "status": station.cng_data.status,
            "last_updated": station.cng_data.last_updated,
            "updated_by": station.cng_data.updated_by
        }

    lpg_out = None
    if station.lpg_data:
        lpg_out = {
            "id": station.lpg_data.id,
            "station_id": station.id,
            "is_available": station.lpg_data.is_available,
            "pressure_bar": station.lpg_data.pressure_bar,
            "price": station.lpg_data.price,
            "status": station.lpg_data.status,
            "last_updated": station.lpg_data.last_updated,
            "updated_by": station.lpg_data.updated_by
        }

    chargers_list = []
    for c in station.chargers:
        chargers_list.append({
            "id": c.id,
            "station_id": c.station_id,
            "charger_type": c.charger_type,
            "connector_type": c.connector_type,
            "total_chargers": c.total_chargers,
            "available_chargers": c.available_chargers,
            "power_kw": c.power_kw,
            "price_per_kwh": c.price_per_kwh,
            "status": c.status,
            "last_updated": c.last_updated,
            "updated_by": c.updated_by
        })

    return {
        "id": station.id,
        "name": station.name,
        "brand": station.brand,
        "description": station.description,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "address": station.address,
        "city": station.city,
        "phone": station.phone,
        "working_hours": station.working_hours,
        "is_open": station.is_open,
        "is_24_7": station.is_24_7,
        "rating": round(station.rating, 1),
        "reviews_count": station.reviews_count,
        "queue_length": station.queue_length,
        "queue_wait_minutes": station.queue_wait_minutes,
        "created_at": station.created_at,
        "updated_at": station.updated_at,
        "updated_by": station.updated_by,
        "fuels": fuels_list,
        "cng_data": cng_out,
        "lpg_data": lpg_out,
        "chargers": chargers_list,
        "distance_km": distance,
        "estimated_time_mins": est_time,
        "has_cng": has_cng,
        "has_lpg": has_lpg,
        "has_ev": has_ev,
        "has_fuel": has_fuel
    }

def get_filtered_stations(
    db: Session,
    search: Optional[str] = None,
    city: Optional[str] = None,
    fuel_code: Optional[str] = None,
    only_cng: bool = False,
    only_lpg: bool = False,
    only_ev: bool = False,
    only_gasoline: bool = False,
    only_diesel: bool = False,
    only_open: bool = False,
    only_24_7: bool = False,
    min_cng_pressure: Optional[float] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    sort_by: Optional[str] = "nearest"
) -> List[Dict[str, Any]]:
    """Query stations from database and apply filters and ranking."""
    query = db.query(Station).options(
        joinedload(Station.fuels).joinedload(StationFuel.fuel_type),
        joinedload(Station.cng_data),
        joinedload(Station.lpg_data),
        joinedload(Station.chargers)
    )

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (Station.name.ilike(s)) |
            (Station.brand.ilike(s)) |
            (Station.address.ilike(s)) |
            (Station.city.ilike(s))
        )

    if city and city.lower() != "all":
        query = query.filter(Station.city.ilike(f"%{city}%"))

    if only_open:
        query = query.filter(Station.is_open == True)

    if only_24_7:
        query = query.filter(Station.is_24_7 == True)

    stations = query.all()
    results = []

    for st in stations:
        data = enrich_station_data(st, user_lat, user_lon)
        
        # Apply specialized filters
        if only_cng:
            if not data["cng_data"] or not data["cng_data"]["is_available"]:
                continue
            if min_cng_pressure and data["cng_data"]["pressure_bar"] < min_cng_pressure:
                continue

        if only_lpg:
            if not data["lpg_data"] or not data["lpg_data"]["is_available"]:
                continue

        if only_ev:
            if not data["chargers"] or len(data["chargers"]) == 0:
                continue

        if only_gasoline:
            has_gas = any(f["is_available"] and f.get("fuel_code", "").startswith("ai_") for f in data["fuels"])
            if not has_gas:
                continue

        if only_diesel:
            has_diesel = any(f["is_available"] and f.get("fuel_code") == "diesel" for f in data["fuels"])
            if not has_diesel:
                continue

        if fuel_code:
            code = fuel_code.lower()
            if code == "cng":
                if not data["cng_data"] or not data["cng_data"]["is_available"]:
                    continue
            elif code == "lpg":
                if not data["lpg_data"] or not data["lpg_data"]["is_available"]:
                    continue
            elif code == "ev":
                if not data["chargers"]:
                    continue
            else:
                has_target = any(f["is_available"] and f.get("fuel_code") == code for f in data["fuels"])
                if not has_target:
                    continue

        results.append(data)

    # Sorting
    if sort_by == "nearest" and user_lat is not None and user_lon is not None:
        results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 99999))
    elif sort_by == "rating":
        results.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "queue":
        results.sort(key=lambda x: (x["queue_wait_minutes"] if x["queue_wait_minutes"] is not None else 999))
    elif sort_by == "cng_pressure":
        results.sort(key=lambda x: (x["cng_data"]["pressure_bar"] if x["cng_data"] else 0), reverse=True)
    elif sort_by == "cheapest" and fuel_code:
        code = fuel_code.lower()
        def get_price(item):
            if code == "cng" and item["cng_data"]:
                return item["cng_data"]["price"]
            if code == "lpg" and item["lpg_data"]:
                return item["lpg_data"]["price"]
            for f in item["fuels"]:
                if f["fuel_code"] == code and f["is_available"]:
                    return f["price"]
            return 999999
        results.sort(key=get_price)

    return results
