"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6)
    role: str = Field(pattern="^(admin|officer)$")


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


# ---------- Zones ----------
class ZoneCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: str = ""


class ZoneOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


# ---------- Settings ----------
class ThresholdUpdate(BaseModel):
    threshold: float = Field(ge=0.05, le=0.95)


class ThresholdOut(BaseModel):
    threshold: float


# ---------- Detection ----------
class DetectRequest(BaseModel):
    video_id: str
    zone_id: int
    frame_skip: int = Field(default=5, ge=1, le=60)  # process every Nth frame


class DetectResult(BaseModel):
    job_id: str
    frames_processed: int
    incidents_created: int
    elapsed_seconds: float


# ---------- Incidents ----------
class IncidentOut(BaseModel):
    id: int
    timestamp: datetime
    violation_type: str
    zone_id: int
    zone_name: Optional[str] = None
    confidence: float
    camera_location: str
    evidence_path: str

    class Config:
        from_attributes = True


class IncidentFilter(BaseModel):
    date_from: Optional[str] = None  # YYYY-MM-DD
    date_to: Optional[str] = None
    zone_id: Optional[int] = None
    violation_type: Optional[str] = None


# ---------- Analytics ----------
class AnalyticsSummary(BaseModel):
    total_incidents: int
    by_type: dict
    by_zone: dict
    by_day: dict
