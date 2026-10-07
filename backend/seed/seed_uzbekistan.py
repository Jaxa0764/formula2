import sys
import os
from datetime import datetime, timedelta
import random

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole, FuelType, Station, StationFuel,
    CNGData, LPGData, EVCharger, Review, PriceHistory,
    SystemAlert, AlertSeverity, ModerationStatus
)
from app.utils.security import hash_password

def seed():
    print("🚀 Initializing SmartFuel Uzbekistan Seed Data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data if any
    db.query(PriceHistory).delete()
    db.query(Review).delete()
    db.query(SystemAlert).delete()
    db.query(EVCharger).delete()
    db.query(CNGData).delete()
    db.query(LPGData).delete()
    db.query(StationFuel).delete()
    db.query(Station).delete()
    db.query(FuelType).delete()
    db.query(User).delete()
    db.commit()

    # 1. Users
    users_data = [
        {"name": "Aziz Rahimov (Super Admin)", "email": "admin@smartfuel.uz", "role": UserRole.SUPER_ADMIN.value, "phone": "+998 90 123 45 67"},
        {"name": "Jamshid Moderator", "email": "moderator@smartfuel.uz", "role": UserRole.MODERATOR.value, "phone": "+998 91 234 56 78"},
        {"name": "Sherzod Station Manager", "email": "manager@smartfuel.uz", "role": UserRole.STATION_MANAGER.value, "phone": "+998 93 345 67 89"},
        {"name": "Sardor Haydovchi", "email": "user@smartfuel.uz", "role": UserRole.USER.value, "phone": "+998 97 456 78 90"}
    ]
    created_users = []
    for u in users_data:
        pwd = "admin123" if "admin" in u["email"] else "user123"
        user = User(
            name=u["name"],
            email=u["email"],
            phone=u["phone"],
            password_hash=hash_password(pwd),
            role=u["role"],
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        db.add(user)
        created_users.append(user)
    db.commit()
    print("✅ Users seeded.")

    # 2. Fuel Types
    fuel_types_data = [
        {"code": "ai_80", "name": "AI-80", "category": "gasoline", "unit": "litr"},
        {"code": "ai_91", "name": "AI-91", "category": "gasoline", "unit": "litr"},
        {"code": "ai_92", "name": "AI-92", "category": "gasoline", "unit": "litr"},
        {"code": "ai_95", "name": "AI-95", "category": "gasoline", "unit": "litr"},
        {"code": "ai_98", "name": "AI-98", "category": "gasoline", "unit": "litr"},
        {"code": "diesel", "name": "Dizel", "category": "diesel", "unit": "litr"},
        {"code": "cng", "name": "Metan (CNG)", "category": "gas", "unit": "m³"},
        {"code": "lpg", "name": "Propan (LPG)", "category": "gas", "unit": "litr"}
    ]
    fuel_types_map = {}
    for ft_data in fuel_types_data:
        ft = FuelType(**ft_data)
        db.add(ft)
        db.commit()
        db.refresh(ft)
        fuel_types_map[ft.code] = ft
    print("✅ Fuel Types seeded.")

    # 3. Realistic Stations in Uzbekistan
    stations_info = [
        {
            "name": "UNG Petro Chilonzor",
            "brand": "UNG Petro",
            "description": "Zamonaviy ko'p tarmoqli avtoyoqilg'i quyish shoxobchasi. Yuqori sifatli AI-92, AI-95 va barqaror yuqori bosimli metan gazi.",
            "latitude": 41.278540,
            "longitude": 69.208750,
            "address": "Chilonzor tumani, Bunyodkor shoh ko'chasi 42",
            "city": "Tashkent",
            "phone": "+998 71 200 01 01",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.8,
            "reviews_count": 42,
            "queue_length": 3,
            "queue_wait_minutes": 6,
            "cng": {"pressure": 205.0, "price": 3750.0, "status": "available"},
            "lpg": {"pressure": 12.5, "price": 5100.0, "status": "available"},
            "fuels": [
                {"code": "ai_80", "price": 7600.0},
                {"code": "ai_92", "price": 10500.0},
                {"code": "ai_95", "price": 13200.0},
                {"code": "diesel", "price": 12400.0}
            ],
            "ev": None
        },
        {
            "name": "UNG Petro Yunusobod Hub",
            "brand": "UNG Petro",
            "description": "Premial AI-95, AI-98 va TokBor tezyurar elektromobil quvvatlash stansiyasi.",
            "latitude": 41.362150,
            "longitude": 69.288420,
            "address": "Yunusobod tumani, Amir Temur ko'chasi 108",
            "city": "Tashkent",
            "phone": "+998 71 200 01 02",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.9,
            "reviews_count": 68,
            "queue_length": 2,
            "queue_wait_minutes": 4,
            "cng": None,
            "lpg": None,
            "fuels": [
                {"code": "ai_92", "price": 10800.0},
                {"code": "ai_95", "price": 13500.0},
                {"code": "ai_98", "price": 16800.0}
            ],
            "ev": {
                "charger_type": "Ultra-Fast DC",
                "connector_type": "CCS2 & GBT",
                "total_chargers": 4,
                "available_chargers": 3,
                "power_kw": 160.0,
                "price_per_kwh": 2400.0,
                "status": "available"
            }
        },
        {
            "name": "Iglik Metan Gaz Sergeli",
            "brand": "Iglik Gaz",
            "description": "Eng yuqori bosimli metan shoxobchasi. Qulay kirish yo'laklari, 16 ta gaz tarqatish kolonkasi.",
            "latitude": 41.229150,
            "longitude": 69.222340,
            "address": "Sergeli tumani, Yangi Sergeli aylanma yo'li",
            "city": "Tashkent",
            "phone": "+998 90 999 11 22",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.7,
            "reviews_count": 55,
            "queue_length": 5,
            "queue_wait_minutes": 10,
            "cng": {"pressure": 218.0, "price": 3700.0, "status": "available"},
            "lpg": {"pressure": 12.0, "price": 5050.0, "status": "available"},
            "fuels": [],
            "ev": None
        },
        {
            "name": "Carvon Oil Mirzo Ulug'bek",
            "brand": "Carvon Oil",
            "description": "Tozalangan AI-92 import yoqilg'isi va Megawatt tezkor quvvatlash kompleksi.",
            "latitude": 41.334200,
            "longitude": 69.345600,
            "address": "Mirzo Ulug'bek shoh ko'chasi 88",
            "city": "Tashkent",
            "phone": "+998 71 267 89 00",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.6,
            "reviews_count": 31,
            "queue_length": 4,
            "queue_wait_minutes": 8,
            "cng": None,
            "lpg": {"pressure": 12.2, "price": 5200.0, "status": "available"},
            "fuels": [
                {"code": "ai_91", "price": 9600.0},
                {"code": "ai_92", "price": 10600.0},
                {"code": "ai_95", "price": 13400.0},
                {"code": "diesel", "price": 12300.0}
            ],
            "ev": {
                "charger_type": "Fast DC",
                "connector_type": "CCS2",
                "total_chargers": 2,
                "available_chargers": 1,
                "power_kw": 120.0,
                "price_per_kwh": 2500.0,
                "status": "available"
            }
        },
        {
            "name": "Missir Oil Shayxontohur",
            "brand": "Missir Oil",
            "description": "Shahar markazidagi qulay joylashuv. Navbatsiz tezkor xizmat ko'rsatish.",
            "latitude": 41.321800,
            "longitude": 69.245200,
            "address": "Shayxontohur tumani, Alisher Navoiy ko'chasi 21",
            "city": "Tashkent",
            "phone": "+998 71 244 55 66",
            "working_hours": "06:00 - 00:00",
            "is_open": True,
            "is_24_7": False,
            "rating": 4.5,
            "reviews_count": 27,
            "queue_length": 1,
            "queue_wait_minutes": 2,
            "cng": None,
            "lpg": None,
            "fuels": [
                {"code": "ai_80", "price": 7500.0},
                {"code": "ai_92", "price": 10400.0},
                {"code": "ai_95", "price": 13100.0}
            ],
            "ev": None
        },
        {
            "name": "TokBor Superhub Yakkasaroy",
            "brand": "TokBor",
            "description": "O'zbekistondagi eng yirik zamonaviy elektromobillar quvvatlash markazi. Kafe, Wi-Fi va dam olish xonasi.",
            "latitude": 41.285400,
            "longitude": 69.256300,
            "address": "Yakkasaroy tumani, Shota Rustaveli ko'chasi 54",
            "city": "Tashkent",
            "phone": "+998 78 777 88 99",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.9,
            "reviews_count": 89,
            "queue_length": 0,
            "queue_wait_minutes": 0,
            "cng": None,
            "lpg": None,
            "fuels": [],
            "ev": {
                "charger_type": "Super Fast DC",
                "connector_type": "CCS2, GBT DC, Type 2",
                "total_chargers": 8,
                "available_chargers": 6,
                "power_kw": 180.0,
                "price_per_kwh": 2350.0,
                "status": "available"
            }
        },
        {
            "name": "Metan Gaz Bektemir (Past Bosim)",
            "brand": "UNG Metan",
            "description": "Bektemir trassasidagi CNG shoxobchasi. Diqqat: Magistral ta'miri sababli bosim pasaygan.",
            "latitude": 41.231200,
            "longitude": 69.341200,
            "address": "Bektemir tumani, Ohangaron shossesi 5",
            "city": "Tashkent",
            "phone": "+998 90 111 22 33",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 3.9,
            "reviews_count": 48,
            "queue_length": 14,
            "queue_wait_minutes": 35,
            "cng": {"pressure": 128.0, "price": 3750.0, "status": "low_pressure"},
            "lpg": None,
            "fuels": [],
            "ev": None
        },
        # Samarkand
        {
            "name": "UNG Petro Samarqand Registon",
            "brand": "UNG Petro",
            "description": "Samarqand shahar markazidagi to'liq xizmat ko'rsatish shoxobchasi va EV zaryadlash nuqtasi.",
            "latitude": 39.654200,
            "longitude": 66.975800,
            "address": "Samarqand shahri, Registon ko'chasi 15",
            "city": "Samarkand",
            "phone": "+998 66 233 44 55",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.7,
            "reviews_count": 39,
            "queue_length": 2,
            "queue_wait_minutes": 5,
            "cng": {"pressure": 198.0, "price": 3800.0, "status": "available"},
            "lpg": {"pressure": 12.0, "price": 5250.0, "status": "available"},
            "fuels": [
                {"code": "ai_91", "price": 9650.0},
                {"code": "ai_92", "price": 10700.0},
                {"code": "ai_95", "price": 13600.0}
            ],
            "ev": {
                "charger_type": "Fast DC",
                "connector_type": "CCS2",
                "total_chargers": 2,
                "available_chargers": 2,
                "power_kw": 80.0,
                "price_per_kwh": 2500.0,
                "status": "available"
            }
        },
        {
            "name": "Afrosiyob Metan Gaz Samarqand",
            "brand": "Afrosiyob Gaz",
            "description": "M39 xalqaro trassasidagi zamonaviy gaz to'ldirish kompressor stansiyasi (AGTKSh).",
            "latitude": 39.689000,
            "longitude": 66.921000,
            "address": "Samarqand aylanma yo'li M39, 4-km",
            "city": "Samarkand",
            "phone": "+998 66 210 20 30",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.8,
            "reviews_count": 52,
            "queue_length": 4,
            "queue_wait_minutes": 8,
            "cng": {"pressure": 210.0, "price": 3750.0, "status": "available"},
            "lpg": {"pressure": 12.4, "price": 5150.0, "status": "available"},
            "fuels": [],
            "ev": None
        },
        # Bukhara
        {
            "name": "Buxoro Neft Gaz Kogon Yo'li",
            "brand": "Buxoro Neft",
            "description": "Buxoro-Kogon magistralidagi barcha turdagi yoqilg'i va metan xizmati.",
            "latitude": 39.764500,
            "longitude": 64.442100,
            "address": "Buxoro shahri, Kogon shossesi 7",
            "city": "Bukhara",
            "phone": "+998 65 221 11 00",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.6,
            "reviews_count": 34,
            "queue_length": 3,
            "queue_wait_minutes": 6,
            "cng": {"pressure": 202.0, "price": 3800.0, "status": "available"},
            "lpg": {"pressure": 12.0, "price": 5200.0, "status": "available"},
            "fuels": [
                {"code": "ai_80", "price": 7600.0},
                {"code": "ai_92", "price": 10650.0},
                {"code": "diesel", "price": 12450.0}
            ],
            "ev": None
        },
        {
            "name": "Somoniy EV Hub Buxoro",
            "brand": "UzAuto Charging",
            "description": "Tarixiy markaz yaqinidagi yashil transport quvvatlash markazi.",
            "latitude": 39.778900,
            "longitude": 64.412300,
            "address": "Buxoro shahri, Ismoil Somoniy ko'chasi 45",
            "city": "Bukhara",
            "phone": "+998 65 240 50 60",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.9,
            "reviews_count": 29,
            "queue_length": 0,
            "queue_wait_minutes": 0,
            "cng": None,
            "lpg": None,
            "fuels": [],
            "ev": {
                "charger_type": "Fast DC",
                "connector_type": "CCS2 & GBT",
                "total_chargers": 3,
                "available_chargers": 2,
                "power_kw": 120.0,
                "price_per_kwh": 2450.0,
                "status": "available"
            }
        },
        # Fergana
        {
            "name": "Farg'ona Oltiariq Metan Gaz",
            "brand": "Vodiy Gaz",
            "description": "Farg'ona vodiysidagi eng zamonaviy gaz kompressor stansiyalaridan biri.",
            "latitude": 40.386400,
            "longitude": 71.786500,
            "address": "Marg'ilon yo'li, Farg'ona aylanma trassasi",
            "city": "Fergana",
            "phone": "+998 73 244 12 12",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.8,
            "reviews_count": 63,
            "queue_length": 4,
            "queue_wait_minutes": 7,
            "cng": {"pressure": 215.0, "price": 3700.0, "status": "available"},
            "lpg": {"pressure": 12.5, "price": 5100.0, "status": "available"},
            "fuels": [],
            "ev": None
        },
        {
            "name": "UNG Petro Farg'ona Markaz",
            "brand": "UNG Petro",
            "description": "Farg'ona shahar markazida AI-92 va AI-95 yoqilg'i ta'minoti.",
            "latitude": 40.372100,
            "longitude": 71.798900,
            "address": "Farg'ona shahri, Al-Farg'oniy ko'chasi 80",
            "city": "Fergana",
            "phone": "+998 73 222 33 44",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.7,
            "reviews_count": 41,
            "queue_length": 2,
            "queue_wait_minutes": 4,
            "cng": None,
            "lpg": None,
            "fuels": [
                {"code": "ai_92", "price": 10550.0},
                {"code": "ai_95", "price": 13300.0},
                {"code": "diesel", "price": 12350.0}
            ],
            "ev": None
        },
        # Andijan
        {
            "name": "Bobur Metan Gaz Andijon",
            "brand": "Vodiy Gaz",
            "description": "Yuqori o'tkazuvchanlikka ega 20 kolonkali metan AGTKSh.",
            "latitude": 40.782100,
            "longitude": 72.344200,
            "address": "Andijon shahri, Bog'ishamol dahasi 12",
            "city": "Andijan",
            "phone": "+998 74 223 90 90",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.7,
            "reviews_count": 47,
            "queue_length": 5,
            "queue_wait_minutes": 9,
            "cng": {"pressure": 208.0, "price": 3720.0, "status": "available"},
            "lpg": {"pressure": 12.1, "price": 5120.0, "status": "available"},
            "fuels": [],
            "ev": None
        },
        {
            "name": "Andijon TokBor EV Hub",
            "brand": "TokBor",
            "description": "Andijon markazidagi tezyurar elektromobillar zaryadlash stansiyasi.",
            "latitude": 40.771200,
            "longitude": 72.358900,
            "address": "Andijon shahri, Milliy Tiklanish ko'chasi 18",
            "city": "Andijan",
            "phone": "+998 74 230 40 50",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.8,
            "reviews_count": 36,
            "queue_length": 1,
            "queue_wait_minutes": 2,
            "cng": None,
            "lpg": None,
            "fuels": [],
            "ev": {
                "charger_type": "Fast DC",
                "connector_type": "CCS2 & GBT",
                "total_chargers": 3,
                "available_chargers": 2,
                "power_kw": 100.0,
                "price_per_kwh": 2400.0,
                "status": "available"
            }
        },
        # Namangan
        {
            "name": "Namangan Chortoq Gaz Metan",
            "brand": "Vodiy Gaz",
            "description": "Namangan aylanma yo'lidagi toza va barqaror bosimli metan shoxobchasi.",
            "latitude": 41.002300,
            "longitude": 71.672100,
            "address": "Namangan shahri, Kosonsoy yo'li aylanmasi",
            "city": "Namangan",
            "phone": "+998 69 231 12 34",
            "working_hours": "24/7",
            "is_open": True,
            "is_24_7": True,
            "rating": 4.6,
            "reviews_count": 38,
            "queue_length": 4,
            "queue_wait_minutes": 8,
            "cng": {"pressure": 196.0, "price": 3750.0, "status": "available"},
            "lpg": {"pressure": 12.3, "price": 5180.0, "status": "available"},
            "fuels": [
                {"code": "ai_80", "price": 7600.0},
                {"code": "ai_92", "price": 10600.0}
            ],
            "ev": None
        }
    ]

    saved_stations = []
    now = datetime.utcnow()

    for s_info in stations_info:
        st = Station(
            name=s_info["name"],
            brand=s_info["brand"],
            description=s_info["description"],
            latitude=s_info["latitude"],
            longitude=s_info["longitude"],
            address=s_info["address"],
            city=s_info["city"],
            phone=s_info["phone"],
            working_hours=s_info["working_hours"],
            is_open=s_info["is_open"],
            is_24_7=s_info["is_24_7"],
            rating=s_info["rating"],
            reviews_count=s_info["reviews_count"],
            queue_length=s_info["queue_length"],
            queue_wait_minutes=s_info["queue_wait_minutes"],
            created_at=now - timedelta(days=60),
            updated_at=now - timedelta(minutes=random.randint(2, 45)),
            updated_by="admin"
        )
        db.add(st)
        db.commit()
        db.refresh(st)
        saved_stations.append(st)

        # CNG
        if s_info.get("cng"):
            c = s_info["cng"]
            cng = CNGData(
                station_id=st.id,
                is_available=(c["status"] != "unavailable"),
                pressure_bar=c["pressure"],
                price=c["price"],
                status=c["status"],
                last_updated=now - timedelta(minutes=random.randint(1, 20)),
                updated_by="admin"
            )
            db.add(cng)

        # LPG
        if s_info.get("lpg"):
            l = s_info["lpg"]
            lpg = LPGData(
                station_id=st.id,
                is_available=True,
                pressure_bar=l["pressure"],
                price=l["price"],
                status=l["status"],
                last_updated=now - timedelta(minutes=random.randint(1, 25)),
                updated_by="admin"
            )
            db.add(lpg)

        # Fuels
        for f in s_info.get("fuels", []):
            ft = fuel_types_map.get(f["code"])
            if ft:
                sf = StationFuel(
                    station_id=st.id,
                    fuel_type_id=ft.id,
                    is_available=True,
                    price=f["price"],
                    quantity_status="normal",
                    last_updated=now - timedelta(minutes=random.randint(5, 60)),
                    updated_by="admin"
                )
                db.add(sf)

                # Generate 30 days price history for trends
                base_price = f["price"]
                for d in range(30, 0, -3):
                    jitter = random.choice([-200.0, -100.0, 0.0, 100.0, 200.0])
                    ph = PriceHistory(
                        station_id=st.id,
                        fuel_type_id=ft.id,
                        price=max(5000.0, base_price + jitter),
                        recorded_at=now - timedelta(days=d)
                    )
                    db.add(ph)

        # EV
        if s_info.get("ev"):
            ev = s_info["ev"]
            charger = EVCharger(
                station_id=st.id,
                charger_type=ev["charger_type"],
                connector_type=ev["connector_type"],
                total_chargers=ev["total_chargers"],
                available_chargers=ev["available_chargers"],
                power_kw=ev["power_kw"],
                price_per_kwh=ev["price_per_kwh"],
                status=ev["status"],
                last_updated=now - timedelta(minutes=random.randint(1, 15)),
                updated_by="admin"
            )
            db.add(charger)

        # Add sample reviews
        comments_uz = [
            "Juda yaxshi zapravka, bosim barqaror va xizmat ko'rsatish tezkor!",
            "Kassirlar xushmuomala, navbat deyarli yo'q, tavsiya qilaman.",
            "Yoqilg'i sifati a'lo darajada, mashina ravon yurmoqda.",
            "Metan bosimi a'lo darajada (210 bar), ballon tez to'ldi."
        ]
        rev = Review(
            station_id=st.id,
            user_id=created_users[3].id,
            rating=round(random.uniform(4.5, 5.0), 1),
            service_rating=5.0,
            cleanliness_rating=5.0,
            queue_rating=4.8,
            fuel_quality_rating=5.0,
            comment=random.choice(comments_uz),
            moderation_status=ModerationStatus.APPROVED.value,
            created_at=now - timedelta(days=random.randint(1, 15))
        )
        db.add(rev)

    # 4. System Alert (Bektemir low pressure)
    alert = SystemAlert(
        severity=AlertSeverity.WARNING.value,
        title="Bektemir CNG: Past gaz bosimi (128 bar)",
        message="Trassadagi profilaktika ishlari tufayli metan bosimi tushib ketgan. Haydovchilarga Sergeli yoki Chilonzor filiallariga murojaat qilish tavsiya etiladi.",
        station_id=saved_stations[6].id,
        is_active=True,
        created_at=now - timedelta(hours=2)
    )
    db.add(alert)

    db.commit()
    db.close()
    print(f"🎉 Successfully seeded {len(saved_stations)} Uzbekistan stations across Tashkent, Samarkand, Bukhara, Fergana, Andijan, and Namangan!")

if __name__ == "__main__":
    seed()
