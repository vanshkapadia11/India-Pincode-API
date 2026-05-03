from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base


class Pincode(Base):
    __tablename__ = "pincodes"

    id = Column(Integer, primary_key=True, index=True)
    pincode = Column(String, index=True, nullable=False)
    post_office = Column(String, nullable=False)
    office_type = Column(String)
    delivery = Column(String)
    division = Column(String)
    region = Column(String)
    circle = Column(String)
    taluk = Column(String)
    district = Column(String, index=True)
    state = Column(String, index=True)
    latitude = Column(Float, nullable=True)  # ← new
    longitude = Column(Float, nullable=True)  # ← new


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    requests_today = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)
