import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.station_service import get_filtered_stations, enrich_station_data
from app.models import Station

def process_ai_query(
    db: Session,
    query: str,
    user_lat: float = 41.311081,
    user_lon: float = 69.240562,
    lang: str = "uz"
) -> Dict[str, Any]:
    """
    Intelligent AI service grounded in real platform database data.
    Understands intent, queries actual database, and provides structured answers with actionable UI buttons.
    """
    q = query.lower().strip()
    
    # 1. Cheapest fuel intent (AI-80, AI-91, AI-92, AI-95, AI-98, Diesel, CNG, LPG)
    fuel_codes = {
        "80": "ai_80",
        "91": "ai_91",
        "92": "ai_92",
        "95": "ai_95",
        "98": "ai_98",
        "dizel": "diesel",
        "diesel": "diesel",
        "metan": "cng",
        "cng": "cng",
        "propan": "lpg",
        "lpg": "lpg"
    }

    target_fuel = None
    for kw, fcode in fuel_codes.items():
        if kw in q:
            target_fuel = fcode
            break

    # Check for keywords
    is_cheapest = any(w in q for w in ["arzon", "дешев", "cheap", "kam narx", "past narx", "eng arzon"])
    is_nearest = any(w in q for w in ["yaqin", "близк", "near", "qayerda", "qaysi biriga", "eng yaqin"])
    is_queue = any(w in q for w in ["navbat", "очеред", "queue", "kutish", "tirband"])
    is_ev = any(w in q for w in ["ev", "elektro", "zaryad", "tok", "электро", "charger", "charg"])
    is_compare = any(w in q for w in ["solishtir", "сравни", "compar", "farqi"])

    actions = []
    stations_data = []
    answer_text = ""
    suggested_questions = []

    if is_compare:
        # Compare nearby stations
        f_type = target_fuel or "cng"
        stations = get_filtered_stations(
            db=db, fuel_code=f_type, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="nearest"
        )[:3]
        if not stations:
            stations = get_filtered_stations(db=db, only_open=True, user_lat=user_lat, user_lon=user_lon)[:3]
            
        if stations:
            lines = []
            for idx, s in enumerate(stations, 1):
                p_info = ""
                if f_type == "cng" and s.get("cng_data"):
                    p_info = f"Metan: {int(s['cng_data']['price']):,} so'm ({s['cng_data']['pressure_bar']} bar)"
                elif f_type == "lpg" and s.get("lpg_data"):
                    p_info = f"Propan: {int(s['lpg_data']['price']):,} so'm"
                else:
                    for f in s.get("fuels", []):
                        if f.get("fuel_code") == f_type:
                            p_info = f"{f['fuel_name']}: {int(f['price']):,} so'm"
                            break
                if not p_info:
                    p_info = f"Reyting: {s['rating']} ⭐"
                lines.append(f"{idx}. **{s['name']}** — {s.get('distance_km', 0)} km ({s.get('estimated_time_mins', 0)} daq.) | {p_info} | Navbat: {s['queue_length']} mashina")
                actions.append({
                    "type": "SHOW_ON_MAP",
                    "station_id": s["id"],
                    "title": f"📍 {s['name']} (Xaritada)"
                })
                stations_data.append(s)

            if lang == "uz":
                answer_text = f"Sizga eng yaqin 3 ta shoxobcha taqqoslashi:\n\n" + "\n\n".join(lines)
            elif lang == "ru":
                answer_text = f"Сравнение 3 ближайших станций:\n\n" + "\n\n".join(lines)
            else:
                answer_text = f"Comparison of 3 closest stations:\n\n" + "\n\n".join(lines)

    elif is_ev or "ev" in q or "elektro" in q:
        # EV Charging intent
        stations = get_filtered_stations(
            db=db, only_ev=True, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="nearest"
        )[:3]
        if stations:
            st = stations[0]
            stations_data = stations
            charger = st["chargers"][0] if st.get("chargers") else {}
            avail = charger.get("available_chargers", 0)
            total = charger.get("total_chargers", 0)
            power = charger.get("power_kw", 0)
            price = charger.get("price_per_kwh", 0)
            
            if lang == "uz":
                answer_text = (
                    f"Sizga eng yaqin EV zaryadlash stansiyasi: **{st['name']}**.\n"
                    f"📍 Masofa: {st.get('distance_km', 1.0)} km (~{st.get('estimated_time_mins', 5)} daqiqa)\n"
                    f"⚡ Bo'sh portlar: **{avail} / {total}** ta ({charger.get('connector_type', 'CCS2')})\n"
                    f"🔋 Quvvat: {power} kW | Narx: {int(price):,} so'm/kWh\n"
                    f"Reyting: {st['rating']} ⭐"
                ).replace(",", " ")
            elif lang == "ru":
                answer_text = (
                    f"Ближайшая зарядная станция для электромобилей: **{st['name']}**.\n"
                    f"📍 Расстояние: {st.get('distance_km', 1.0)} км\n"
                    f"⚡ Свободно: **{avail} / {total}** ({charger.get('connector_type', 'CCS2')})\n"
                    f"🔋 Мощность: {power} кВт | {int(price):,} сум/кВт·ч"
                ).replace(",", " ")
            else:
                answer_text = (
                    f"Nearest EV charging hub: **{st['name']}**.\n"
                    f"📍 Distance: {st.get('distance_km', 1.0)} km\n"
                    f"⚡ Available ports: **{avail} / {total}**\n"
                    f"🔋 Power: {power} kW | Price: {int(price):,} UZS/kWh"
                ).replace(",", " ")

            actions.append({"type": "BUILD_ROUTE", "station_id": st["id"], "title": "🚀 Marshrut tuzish"})
            actions.append({"type": "SHOW_ON_MAP", "station_id": st["id"], "title": "📍 Xaritada ko'rsatish"})
        else:
            answer_text = "Hozirda bo'sh EV zaryadlash stansiyalari topilmadi."

    elif is_cheapest and target_fuel:
        # Cheapest fuel
        stations = get_filtered_stations(
            db=db, fuel_code=target_fuel, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="cheapest"
        )
        if stations:
            best = stations[0]
            stations_data = stations[:2]
            
            # Find price
            p = 0
            if target_fuel == "cng" and best.get("cng_data"):
                p = best["cng_data"]["price"]
                extra = f"Bosim: {best['cng_data']['pressure_bar']} bar"
            elif target_fuel == "lpg" and best.get("lpg_data"):
                p = best["lpg_data"]["price"]
                extra = f"Bosim: {best['lpg_data']['pressure_bar']} bar"
            else:
                extra = ""
                for f in best.get("fuels", []):
                    if f.get("fuel_code") == target_fuel:
                        p = f["price"]
                        break
                        
            if lang == "uz":
                answer_text = (
                    f"Eng arzon {target_fuel.upper().replace('_', '-')} **{best['name']}** zapravkasida!\n"
                    f"💰 Narx: **{int(p):,} so'm**\n"
                    f"📍 Masofa: {best.get('distance_km', 0)} km (~{best.get('estimated_time_mins', 0)} daqiqa)\n"
                    f"Manzil: {best['address']}\n"
                    f"{extra}"
                ).replace(",", " ")
            elif lang == "ru":
                answer_text = (
                    f"Самое дешевое топливо {target_fuel.upper()} на АЗС **{best['name']}**!\n"
                    f"💰 Цена: **{int(p):,} сум**\n"
                    f"📍 Расстояние: {best.get('distance_km', 0)} км\n"
                    f"Адрес: {best['address']}"
                ).replace(",", " ")
            else:
                answer_text = (
                    f"Cheapest {target_fuel.upper()} is at **{best['name']}**!\n"
                    f"💰 Price: **{int(p):,} UZS**\n"
                    f"📍 Distance: {best.get('distance_km', 0)} km\n"
                    f"Address: {best['address']}"
                ).replace(",", " ")

            actions.append({"type": "BUILD_ROUTE", "station_id": best["id"], "title": "🚀 Marshrut tuzish"})
            actions.append({"type": "SHOW_ON_MAP", "station_id": best["id"], "title": "📍 Xaritada ko'rsatish"})
            actions.append({"type": "VIEW_STATION", "station_id": best["id"], "title": "ℹ️ Batafsil"})
        else:
            answer_text = f"Kechirasiz, ma'lumotlar bazasida {target_fuel.upper()} bo'yicha ma'lumot topilmadi."

    elif is_queue:
        # Shortest queue
        stations = get_filtered_stations(
            db=db, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="queue"
        )
        if stations:
            best = stations[0]
            stations_data = stations[:2]
            if lang == "uz":
                answer_text = (
                    f"Eng kam navbatli zapravka: **{best['name']}**.\n"
                    f"🚗 Navbat: atigi **{best['queue_length']} ta avtomobil**\n"
                    f"⏱ Taxminiy kutish: **{best['queue_wait_minutes']} daqiqa**\n"
                    f"📍 Masofa: {best.get('distance_km', 0)} km"
                )
            elif lang == "ru":
                answer_text = (
                    f"Наименьшая очередь на АЗС **{best['name']}**.\n"
                    f"🚗 В очереди: всего **{best['queue_length']} авто**\n"
                    f"⏱ Ожидание: **{best['queue_wait_minutes']} мин**\n"
                    f"📍 Расстояние: {best.get('distance_km', 0)} км"
                )
            else:
                answer_text = (
                    f"Shortest queue is at **{best['name']}**.\n"
                    f"🚗 Vehicles waiting: **{best['queue_length']} cars**\n"
                    f"⏱ Est. wait time: **{best['queue_wait_minutes']} mins**\n"
                    f"📍 Distance: {best.get('distance_km', 0)} km"
                )
            actions.append({"type": "BUILD_ROUTE", "station_id": best["id"], "title": "🚀 Marshrut tuzish"})
            actions.append({"type": "SHOW_ON_MAP", "station_id": best["id"], "title": "📍 Xaritada ko'rsatish"})
    else:
        # Default or Nearest CNG / General station recommendation
        fuel_filter = target_fuel or "cng"
        stations = get_filtered_stations(
            db=db, fuel_code=fuel_filter, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="nearest"
        )
        if not stations:
            stations = get_filtered_stations(db=db, only_open=True, user_lat=user_lat, user_lon=user_lon, sort_by="nearest")
            
        if stations:
            st = stations[0]
            stations_data = stations[:2]
            pressure_info = f"CNG Bosimi: {st['cng_data']['pressure_bar']} bar | " if st.get("cng_data") else ""
            if lang == "uz":
                answer_text = (
                    f"Sizga eng yaqin shoxobcha: **{st['name']}** ({st['brand'] or 'Zapravka'}).\n"
                    f"📍 Masofa: {st.get('distance_km', 0)} km (~{st.get('estimated_time_mins', 5)} daqiqa)\n"
                    f"{pressure_info}Reyting: {st['rating']} ⭐\n"
                    f"Manzil: {st['address']}"
                )
            elif lang == "ru":
                answer_text = (
                    f"Ближайшая станция: **{st['name']}**.\n"
                    f"📍 Расстояние: {st.get('distance_km', 0)} км (~{st.get('estimated_time_mins', 5)} мин)\n"
                    f"{pressure_info}Рейтинг: {st['rating']} ⭐\n"
                    f"Адрес: {st['address']}"
                )
            else:
                answer_text = (
                    f"Nearest station: **{st['name']}**.\n"
                    f"📍 Distance: {st.get('distance_km', 0)} km (~{st.get('estimated_time_mins', 5)} min)\n"
                    f"{pressure_info}Rating: {st['rating']} ⭐\n"
                    f"Address: {st['address']}"
                )
            actions.append({"type": "BUILD_ROUTE", "station_id": st["id"], "title": "🚀 Marshrut tuzish"})
            actions.append({"type": "SHOW_ON_MAP", "station_id": st["id"], "title": "📍 Xaritada ko'rsatish"})
            actions.append({"type": "VIEW_STATION", "station_id": st["id"], "title": "ℹ️ Batafsil"})
        else:
            answer_text = "Hozirda yaqin hududda ochiq zapravkalar topilmadi."

    suggested_questions = [
        "Eng arzon AI-92 qayerda?",
        "Yaqin metan (CNG) zapravkani top",
        "Bo'sh EV zaryadkalar qayerda?",
        "Navbatsiz zapravkalar"
    ]

    return {
        "answer": answer_text,
        "actions": actions,
        "stations": stations_data,
        "suggested_questions": suggested_questions
    }
