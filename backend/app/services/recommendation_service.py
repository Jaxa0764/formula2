from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.services.station_service import get_filtered_stations

def calculate_best_option(
    db: Session,
    fuel_code: str = "cng",
    user_lat: float = 41.311081,
    user_lon: float = 69.240562,
    lang: str = "uz"
) -> Optional[Dict[str, Any]]:
    """
    Calculate the Best Option recommendation balancing distance, price, pressure, rating, and queue.
    Returns the top recommended station with clear justification.
    """
    stations = get_filtered_stations(
        db=db,
        fuel_code=fuel_code,
        only_open=True,
        user_lat=user_lat,
        user_lon=user_lon,
        sort_by="nearest"
    )

    if not stations:
        # Fallback to all stations open
        stations = get_filtered_stations(
            db=db,
            only_open=True,
            user_lat=user_lat,
            user_lon=user_lon,
            sort_by="nearest"
        )
        if not stations:
            return None

    # Find price bounds
    prices = []
    for st in stations:
        if fuel_code == "cng" and st.get("cng_data"):
            prices.append(st["cng_data"]["price"])
        elif fuel_code == "lpg" and st.get("lpg_data"):
            prices.append(st["lpg_data"]["price"])
        else:
            for f in st.get("fuels", []):
                if f.get("fuel_code") == fuel_code:
                    prices.append(f["price"])
    min_price = min(prices) if prices else 1.0
    max_price = max(prices) if prices else 1.0
    price_range = max(1.0, max_price - min_price)

    scored_stations = []

    for st in stations:
        dist = st.get("distance_km") or 5.0
        rating = st.get("rating") or 4.0
        queue_wait = st.get("queue_wait_minutes") or 0
        queue_len = st.get("queue_length") or 0
        
        # Determine price for target fuel
        price = None
        if fuel_code == "cng" and st.get("cng_data"):
            price = st["cng_data"]["price"]
        elif fuel_code == "lpg" and st.get("lpg_data"):
            price = st["lpg_data"]["price"]
        else:
            for f in st.get("fuels", []):
                if f.get("fuel_code") == fuel_code:
                    price = f["price"]
                    break
        
        if price is None and prices:
            price = sum(prices) / len(prices)
        elif price is None:
            price = 10000.0

        # Component scores (0 to 100)
        # Distance score: closer is better
        dist_score = max(0.0, 100.0 - (dist * 7.5))
        
        # Price score: lower is better
        price_norm = (price - min_price) / price_range if price_range > 0 else 0
        price_score = max(0.0, 100.0 - (price_norm * 100.0))
        
        # Rating score: 5.0 -> 100
        rating_score = (rating / 5.0) * 100.0
        
        # Queue score: less waiting is better
        queue_score = max(0.0, 100.0 - (queue_wait * 4.0))
        
        # CNG pressure score
        pressure_score = 100.0
        if fuel_code == "cng" and st.get("cng_data"):
            p_bar = st["cng_data"]["pressure_bar"]
            if p_bar >= 200:
                pressure_score = 100.0
            elif p_bar >= 170:
                pressure_score = 80.0
            elif p_bar >= 140:
                pressure_score = 50.0
            else:
                pressure_score = 10.0

        # Weighted combination
        # Dist 35%, Price 25%, Queue 15%, Rating 10%, Pressure/EV availability 15%
        total_score = (
            dist_score * 0.35 +
            price_score * 0.25 +
            queue_score * 0.15 +
            rating_score * 0.10 +
            pressure_score * 0.15
        )

        # Formulate human-readable reasons
        reasons = []
        if dist <= 3.0:
            reasons.append(f"Juda yaqin masofa ({dist} km, ~{st.get('estimated_time_mins', 5)} daqiqa)" if lang == "uz" else f"Очень близко ({dist} км)" if lang == "ru" else f"Very close ({dist} km)")
        elif dist <= 6.0:
            reasons.append(f"Qulay masofa ({dist} km)" if lang == "uz" else f"Удобное расстояние ({dist} км)" if lang == "ru" else f"Convenient distance ({dist} km)")

        if price <= min_price * 1.02:
            reasons.append(f"Eng arzon narx ({int(price):,} so'm)".replace(",", " ") if lang == "uz" else f"Самая низкая цена ({int(price):,} сум)" if lang == "ru" else f"Best price ({int(price):,} UZS)")

        if fuel_code == "cng" and st.get("cng_data") and st["cng_data"]["pressure_bar"] >= 190:
            reasons.append(f"A'lo bosim ({st['cng_data']['pressure_bar']} bar)" if lang == "uz" else f"Отличное давление ({st['cng_data']['pressure_bar']} бар)" if lang == "ru" else f"Great pressure ({st['cng_data']['pressure_bar']} bar)")

        if queue_len <= 3:
            reasons.append(f"Kichik navbat (faqat {queue_len} ta mashina, ~{queue_wait} daqiqa)" if lang == "uz" else f"Маленькая очередь ({queue_len} машин)" if lang == "ru" else f"Short queue ({queue_len} cars)")

        if rating >= 4.7:
            reasons.append(f"Yuqori reyting ({rating} ⭐)" if lang == "uz" else f"Высокий рейтинг ({rating} ⭐)" if lang == "ru" else f"Top rated ({rating} ⭐)")

        if not reasons:
            reasons.append("Tavsiya etilgan eng maqbul variant" if lang == "uz" else "Оптимальный вариант" if lang == "ru" else "Optimal balanced choice")

        st["best_option_score"] = round(total_score, 1)
        st["best_option_reason"] = ", ".join(reasons)

        scored_stations.append({
            "station": st,
            "score": round(total_score, 1),
            "reasons": reasons
        })

    scored_stations.sort(key=lambda x: x["score"], reverse=True)
    best = scored_stations[0]

    return {
        "station": best["station"],
        "score": best["score"],
        "reasons": best["reasons"],
        "fuel_code": fuel_code,
        "calculated_at": datetime.utcnow()
    }
