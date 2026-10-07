import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    STATION_MANAGER = "station_manager"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class CNGStatus(str, enum.Enum):
    AVAILABLE = "available"
    LOW_PRESSURE = "low_pressure"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"

class LPGStatus(str, enum.Enum):
    AVAILABLE = "available"
    LOW_PRESSURE = "low_pressure"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"

class ChargerStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class ModerationStatus(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.USER.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    notification_preferences = Column(JSON, default=lambda: {"price_alerts": True, "cng_alerts": True, "ev_alerts": True})
    
    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True) # e.g. UNG Petro, TokBor, Carvon
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), default="Tashkent", index=True)
    phone = Column(String(50), nullable=True)
    working_hours = Column(String(100), default="24/7")
    is_open = Column(Boolean, default=True)
    is_24_7 = Column(Boolean, default=True)
    rating = Column(Float, default=4.5)
    reviews_count = Column(Integer, default=0)
    
    # Queue indicators
    queue_length = Column(Integer, default=0) # number of vehicles
    queue_wait_minutes = Column(Integer, default=0) # estimated minutes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default="system")
    
    # Relationships
    fuels = relationship("StationFuel", back_populates="station", cascade="all, delete-orphan")
    cng_data = relationship("CNGData", uselist=False, back_populates="station", cascade="all, delete-orphan")
    lpg_data = relationship("LPGData", uselist=False, back_populates="station", cascade="all, delete-orphan")
    chargers = relationship("EVCharger", back_populates="station", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="station", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="station", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="station", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="station", cascade="all, delete-orphan")

class FuelType(Base):
    __tablename__ = "fuel_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # ai_80, ai_91, ai_92, ai_95, ai_98, diesel, cng, lpg
    name = Column(String(100), nullable=False) # e.g. "AI-92", "Methane (CNG)"
    category = Column(String(50), nullable=False) # gasoline, diesel, gas, electric
    unit = Column(String(20), default="liter") # liter, m3, kwh
    is_active = Column(Boolean, default=True)

class StationFuel(Base):
    __tablename__ = "station_fuels"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey("fuel_types.id", ondelete="CASCADE"), nullable=False, index=True)
    is_available = Column(Boolean, default=True)
    price = Column(Float, nullable=False) # in UZS
    quantity_status = Column(String(50), default="normal") # normal, low, out_of_stock
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), default="admin")
    
    # Relationships
    station = relationship("Station", back_populates="fuels")
    fuel_type = relationship("FuelType")

class CNGData(Base):
    __tablename__ = "cng_data"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    is_available = Column(Boolean, default=True)
    pressure_bar = Column(Float, default=200.0) # in bar, e.g. 195.0
    price = Column(Float, default=3750.0) # in UZS per m3
    status = Column(String(50), default=CNGStatus.AVAILABLE.value)
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), default="admin")
    
    station = relationship("Station", back_populates="cng_data")

class LPGData(Base):
    __tablename__ = "lpg_data"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    is_available = Column(Boolean, default=True)
    pressure_bar = Column(Float, default=12.0) # LPG typical storage bar
    price = Column(Float, default=5200.0) # in UZS per liter
    status = Column(String(50), default=LPGStatus.AVAILABLE.value)
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), default="admin")
    
    station = relationship("Station", back_populates="lpg_data")

class EVCharger(Base):
    __tablename__ = "ev_chargers"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    charger_type = Column(String(50), default="Fast DC") # Fast DC, Ultra-Fast, AC Slow
    connector_type = Column(String(50), default="CCS2") # CCS2, GBT DC, GBT AC, Type 2, CHAdeMO
    total_chargers = Column(Integer, default=2)
    available_chargers = Column(Integer, default=1)
    power_kw = Column(Float, default=120.0) # in kW
    price_per_kwh = Column(Float, default=2400.0) # in UZS per kWh
    status = Column(String(50), default=ChargerStatus.AVAILABLE.value)
    last_updated = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), default="admin")
    
    station = relationship("Station", back_populates="chargers")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False) # 1.0 to 5.0
    service_rating = Column(Float, default=5.0)
    cleanliness_rating = Column(Float, default=5.0)
    queue_rating = Column(Float, default=5.0)
    fuel_quality_rating = Column(Float, default=5.0)
    comment = Column(Text, nullable=True)
    moderation_status = Column(String(50), default=ModerationStatus.APPROVED.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    station = relationship("Station", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="favorites")
    station = relationship("Station", back_populates="favorites")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(100), nullable=False) # incorrect_price, fuel_unavailable, etc.
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending") # pending, reviewed, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reports")
    station = relationship("Station", back_populates="reports")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey("fuel_types.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    station = relationship("Station", back_populates="price_history")
    fuel_type = relationship("FuelType")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="system")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(150), default="system")
    action = Column(String(100), nullable=False) # e.g. UPDATE_PRICE, CREATE_STATION, CNG_PRESSURE_CHANGE
    entity = Column(String(100), nullable=False) # e.g. station_fuels, cng_data, station
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemAlert(Base):
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String(20), default=AlertSeverity.INFO.value) # INFO, WARNING, CRITICAL
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure composite indexes for geospatial and fast querying
Index("idx_station_coords", Station.latitude, Station.longitude)
