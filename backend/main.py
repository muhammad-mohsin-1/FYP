"""FastAPI backend — Restricted Zone Contraband Detection System.

Covers all 11 functional requirements from the approved proposal:
 FR1  auth with RBAC (admin / security officer), bcrypt-hashed passwords
 FR2  zone add / update / remove
 FR3  confidence-threshold slider (runtime setting)
 FR4  video file upload + camera-location (zone) dropdown
 FR5  YOLOv11 multi-class detection loop (smoking + mobile_phone)
 FR6  instant red toast alerts via WebSocket the moment a violation is found
 FR7  automatic incident logging to the database (timestamp, type, zone)
 FR8  evidence frame snapshot (.jpg) saved per incident
 FR9  analytics dashboard data (bar + pie chart aggregations)
 FR10 search / filter incidents by date, zone, violation type
 FR11 one-click PDF compliance report download

Non-functional: <2s frame-to-alert latency target, graceful stream-error
handling, responsive API errors, no hard dependency on GPU hardware.
"""
import os
import shutil
import time
import uuid
from datetime import datetime
from typing import List, Optional

import cv2
from fastapi import (FastAPI, Depends, HTTPException, UploadFile, File,
                     Form, WebSocket, WebSocketDisconnect, Query, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db, init_db
from . import models, schemas
from .auth import (hash_password, verify_password, create_access_token,
                   get_current_user, require_admin, require_officer)
from .detector import get_detector, DEFAULT_CONF
from .reports import generate_pdf
from . import app_config

UPLOAD_DIR = app_config.UPLOAD_DIR
EVIDENCE_DIR = app_config.EVIDENCE_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

app = FastAPI(title="Restricted Zone Contraband Detection API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ---------------- WebSocket alert bus (FR6) ----------------
class AlertBus:
    def __init__(self):
        self.clients: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


alert_bus = AlertBus()


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    """Live alert channel. Frontend shows a RED toast per message."""
    await alert_bus.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; client may ping
    except WebSocketDisconnect:
        alert_bus.disconnect(ws)


# ---------------- helpers ----------------
def get_threshold(db: Session) -> float:
    row = db.query(models.Setting).filter(models.Setting.key == "conf_threshold").first()
    return float(row.value) if row else DEFAULT_CONF


# ---------------- FR1: auth ----------------
@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "role": user.role, "username": user.username}


@app.post("/api/auth/logout")
def logout(user: models.User = Depends(get_current_user)):
    # JWT is stateless; logout = client discards the token.
    return {"message": f"{user.username} logged out (discard token client-side)"}


@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.post("/api/auth/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db),
             admin: models.User = Depends(require_admin)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "Username already exists")
    user = models.User(username=payload.username,
                       password_hash=hash_password(payload.password),
                       role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------- FR2: zones ----------------
@app.get("/api/zones", response_model=List[schemas.ZoneOut])
def list_zones(db: Session = Depends(get_db), user: models.User = Depends(require_officer)):
    return db.query(models.Zone).order_by(models.Zone.name).all()


@app.post("/api/zones", response_model=schemas.ZoneOut, status_code=201)
def create_zone(payload: schemas.ZoneCreate, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    if db.query(models.Zone).filter(models.Zone.name == payload.name).first():
        raise HTTPException(400, "Zone already exists")
    zone = models.Zone(name=payload.name, description=payload.description)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@app.put("/api/zones/{zone_id}", response_model=schemas.ZoneOut)
def update_zone(zone_id: int, payload: schemas.ZoneCreate, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    zone.name = payload.name
    zone.description = payload.description
    db.commit()
    db.refresh(zone)
    return zone


@app.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    db.delete(zone)
    db.commit()
    return {"message": f"Zone '{zone.name}' removed"}


# ---------------- FR3: threshold ----------------
@app.get("/api/settings/threshold", response_model=schemas.ThresholdOut)
def get_threshold_ep(db: Session = Depends(get_db), user: models.User = Depends(require_officer)):
    return {"threshold": get_threshold(db)}


@app.post("/api/settings/threshold", response_model=schemas.ThresholdOut)
def set_threshold(payload: schemas.ThresholdUpdate, db: Session = Depends(get_db),
                  user: models.User = Depends(require_officer)):
    row = db.query(models.Setting).filter(models.Setting.key == "conf_threshold").first()
    if row:
        row.value = str(payload.threshold)
    else:
        db.add(models.Setting(key="conf_threshold", value=str(payload.threshold)))
    db.commit()
    return {"threshold": payload.threshold}


# ---------------- FR4: video upload ----------------
@app.post("/api/videos/upload")
def upload_video(file: UploadFile = File(...), camera_location: str = Form(""),
                 user: models.User = Depends(require_officer)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
        raise HTTPException(400, "Unsupported video format")
    video_id = uuid.uuid4().hex
    path = os.path.join(UPLOAD_DIR, video_id + ext)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"video_id": video_id, "filename": file.filename,
            "camera_location": camera_location, "path": path}


# ---------------- FR5/6/7/8: detection loop ----------------
@app.post("/api/detect/run", response_model=schemas.DetectResult)
async def run_detection(payload: schemas.DetectRequest,
                        db: Session = Depends(get_db),
                        user: models.User = Depends(require_officer)):
    """Run the YOLOv11 detection loop over an uploaded video.

    For every detection above the confidence threshold an incident row is
    written (FR7), an evidence .jpg snapshot is saved (FR8) and a red-toast
    alert is pushed over the WebSocket (FR6). Stream errors are caught so a
    corrupt video can never crash the backend (NFR: graceful handling).
    """
    zone = db.query(models.Zone).get(payload.zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")

    video_path = next((os.path.join(UPLOAD_DIR, f)
                       for f in os.listdir(UPLOAD_DIR)
                       if f.startswith(payload.video_id)), None)
    if not video_path:
        raise HTTPException(404, "Video not found - upload it first")

    try:
        detector = get_detector()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    conf = get_threshold(db)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(400, "Could not open video stream (corrupt or unsupported codec)")

    job_id = uuid.uuid4().hex[:8]
    frames_processed = 0
    incidents_created = 0
    t_start = time.perf_counter()
    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break  # end of stream or read error -> stop gracefully
            frame_idx += 1
            if frame_idx % payload.frame_skip != 0:
                continue
            frames_processed += 1
            try:
                detections, latency_ms = detector.infer_frame(frame, conf=conf)
            except Exception:
                continue  # never let one bad frame kill the loop
            if detections:
                annotated = detector.draw(frame.copy(), detections)
                for d in detections:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    ev_name = f"{payload.zone_id}_{d['class_name']}_{ts}.jpg"
                    ev_path = os.path.join(EVIDENCE_DIR, ev_name)
                    cv2.imwrite(ev_path, annotated)
                    inc = models.Incident(
                        violation_type=d["class_name"],
                        zone_id=zone.id,
                        confidence=d["confidence"],
                        camera_location=zone.name,
                        evidence_path=ev_path,
                    )
                    db.add(inc)
                    db.commit()
                    incidents_created += 1
                    await alert_bus.broadcast({  # FR6: instant red toast
                        "type": "violation",
                        "violation_type": d["class_name"],
                        "zone": zone.name,
                        "confidence": round(d["confidence"], 3),
                        "timestamp": datetime.now().isoformat(),
                        "latency_ms": round(latency_ms, 1),
                        "evidence": ev_name,
                    })
    finally:
        cap.release()

    elapsed = time.perf_counter() - t_start
    return {"job_id": job_id, "frames_processed": frames_processed,
            "incidents_created": incidents_created,
            "elapsed_seconds": round(elapsed, 2)}


@app.get("/api/evidence/{filename}")
def get_evidence(filename: str, user: models.User = Depends(require_officer)):
    path = os.path.join(EVIDENCE_DIR, os.path.basename(filename))
    if not os.path.exists(path):
        raise HTTPException(404, "Evidence file not found")
    return FileResponse(path, media_type="image/jpeg")


# ---------------- FR10: search / filter incidents ----------------
@app.get("/api/incidents", response_model=List[schemas.IncidentOut])
def list_incidents(date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
                   date_to: Optional[str] = Query(None),
                   zone_id: Optional[int] = Query(None),
                   violation_type: Optional[str] = Query(None),
                   db: Session = Depends(get_db),
                   user: models.User = Depends(require_officer)):
    q = db.query(models.Incident).join(models.Zone)
    if date_from:
        q = q.filter(models.Incident.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(models.Incident.timestamp <= datetime.fromisoformat(date_to + "T23:59:59"))
    if zone_id:
        q = q.filter(models.Incident.zone_id == zone_id)
    if violation_type:
        q = q.filter(models.Incident.violation_type == violation_type)
    rows = q.order_by(models.Incident.timestamp.desc()).limit(1000).all()
    out = []
    for r in rows:
        o = schemas.IncidentOut.model_validate(r)
        o.zone_name = r.zone.name
        out.append(o)
    return out


# ---------------- FR9: analytics ----------------
@app.get("/api/analytics/summary", response_model=schemas.AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db),
                      user: models.User = Depends(require_officer)):
    total = db.query(func.count(models.Incident.id)).scalar() or 0
    by_type = {k: v for k, v in db.query(models.Incident.violation_type,
                                         func.count()).group_by(models.Incident.violation_type).all()}
    by_zone = {z: c for z, c in db.query(models.Zone.name, func.count(models.Incident.id))
               .join(models.Incident).group_by(models.Zone.name).all()}
    by_day = {str(d): c for d, c in
              db.query(func.date(models.Incident.timestamp), func.count())
              .group_by(func.date(models.Incident.timestamp))
              .order_by(func.date(models.Incident.timestamp)).all()}
    return {"total_incidents": total, "by_type": by_type, "by_zone": by_zone, "by_day": by_day}


# ---------------- FR11: PDF report ----------------
@app.get("/api/reports/pdf")
def pdf_report(date_from: Optional[str] = Query(None),
               date_to: Optional[str] = Query(None),
               zone_id: Optional[int] = Query(None),
               db: Session = Depends(get_db),
               user: models.User = Depends(require_officer)):
    df = datetime.fromisoformat(date_from) if date_from else None
    dt = datetime.fromisoformat(date_to + "T23:59:59") if date_to else None
    path = generate_pdf(db, date_from=df, date_to=dt, zone_id=zone_id)
    return FileResponse(path, media_type="application/pdf",
                        filename=os.path.basename(path))


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "contraband-detection-api"}


@app.on_event("startup")
def on_startup():
    init_db()
