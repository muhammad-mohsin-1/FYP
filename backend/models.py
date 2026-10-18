"""Database models: users (RBAC), zones, incidents."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # role is either "admin" or "officer" (Security Officer)
    role = Column(String(16), nullable=False, default="officer")
    created_at = Column(DateTime, default=datetime.utcnow)


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)  # e.g. "Server Room"
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("Incident", back_populates="zone")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # violation_type: "mobile_phone" or "smoking"
    violation_type = Column(String(32), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    camera_location = Column(String(128), default="")
    evidence_path = Column(String(512), default="")  # local .jpg snapshot

    zone = relationship("Zone", back_populates="incidents")


class Setting(Base):
    """Single-row key/value store for runtime settings (confidence threshold)."""
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(String(64), nullable=False)
