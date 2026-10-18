# VIVA PREP — Likely Examiner Questions + Short Answers

Project: **Restricted Zone Contraband Detection System**
(YOLOv11 · FastAPI · React.js · MySQL)
Team: Muhammad Mohsin (70148217) · Usman Siddique (70144882) · Hamza Habib Khan (70138335)

---

## AI / Model questions

**Q: Why YOLOv11 and not YOLOv8 / Faster R-CNN?**
A: Faster R-CNN is two-stage (region proposals + classification) — too slow for
real-time video. YOLO is single-stage: one pass predicts boxes + classes.
YOLOv11 is the newest Ultralytics iteration; its C3k2 blocks and improved
feature fusion detect small objects (cigarettes, phones in hand) better at
lower latency than v8, which matters for our <2 s frame-to-alert requirement.

**Q: What does "transfer learning" mean in your project?**
A: We start from `yolo11n.pt` weights pre-trained on COCO (80 classes, 118k
images) instead of random weights. The backbone already knows edges, shapes,
textures; we fine-tune all layers on our 2-class dataset (smoking,
mobile_phone). This converges in far fewer epochs than training from scratch.

**Q: Explain your dataset.**
A: Two verified sources merged into one YOLO-format dataset:
(1) **CigDet** (Mendeley, DOI 10.17632/6hyrr8typ7.1) — 557 YOLO-annotated
cigarette images → class `0` (smoking); (2) **COCO 2017** `cell phone`
(category_id 67) subset, up to 400 images, boxes converted from COCO
`[x,y,w,h]` to YOLO normalized format → class `1` (mobile_phone).
CigDet train→train / test→val; COCO phones 80/20. See `docs/DATASETS.md`.

**Q: What are precision, recall, mAP?**
A: Precision = TP/(TP+FP): of all detections, how many were correct.
Recall = TP/(TP+FN): of all real objects, how many we found.
mAP50 = mean Average Precision at IoU 0.50, averaged over classes — the
standard detection metric. mAP50-95 averages over IoU 0.50–0.95 (stricter).

**Q: Your CPU training only ran 5 epochs — is that a real model?**
A: Honestly: the 5-epoch CPU run **validates the pipeline end-to-end**
(data loading, loss decreasing, metrics computed, weights exported). It is
not production-grade. The production model follows
`ai/full_training_recipe_COLAB.md`: 100 epochs, imgsz 640, batch 16 on a
Colab T4 GPU. Our report states this explicitly.

**Q: What augmentation did you use?**
A: YOLOv11 defaults: HSV jitter, horizontal flip, translation, scaling,
mosaic (combines 4 images — helps small objects like cigarettes). Listed
with values in the Colab recipe.

**Q: How do you handle false positives (e.g., a pen mistaken for a cigarette)?**
A: Three layers: (1) the FR3 confidence-threshold slider lets security staff
raise the cutoff at runtime; (2) every detection is logged with its
confidence so low-confidence patterns are auditable; (3) the production
recipe adds the 2,337-image Roboflow smoking dataset to harden the smoking
class. Future work: temporal smoothing (require detection in N consecutive
frames).

## Backend questions

**Q: Why FastAPI instead of Flask/Django?**
A: FastAPI is async-native (handles the video loop + WebSocket alerts +
DB writes concurrently), has automatic OpenAPI docs, and Pydantic validation.
Flask would need extra extensions for the same; Django is heavier than needed.

**Q: How does authentication work?**
A: `POST /api/auth/login` checks the username, verifies the password with
**bcrypt** (`passlib`), and returns a **JWT** (signed with HS256). The React
app sends it as `Authorization: Bearer <token>`. `require_admin` /
`require_officer` dependencies enforce RBAC per endpoint. Passwords are
**never stored in plain text** — only bcrypt hashes.

**Q: Why SQLite locally but MySQL in the proposal?**
A: Same SQLAlchemy models and code; `DATABASE_URL` switches the engine.
SQLite was used for local validation (low-RAM VM); production uses MySQL
8.0 via `docker-compose.yml`, exactly as proposed. The schema is identical.

**Q: What happens if the video file is corrupt?**
A: `cv2.VideoCapture.isOpened()` is checked → clean HTTP 400. Inside the
loop, each frame's inference is wrapped in try/except and a failed `read()`
breaks the loop gracefully. The backend never crashes on a bad stream
(non-functional requirement: graceful stream-error handling).

**Q: How do "instant" alerts work?**
A: `WS /ws/alerts` WebSocket. The moment the detection loop logs an
incident, the backend `await alert_bus.broadcast(...)` pushes a JSON event;
React's `react-hot-toast` renders it as a **red toast**. Measured
frame-to-alert is well under the 2 s budget (YOLOv11n ≈ 80–200 ms/frame CPU).

## Frontend / system questions

**Q: How do Admin and Security Officer differ?**
A: Both log in the same way. Officers can monitor, upload videos, tune the
threshold, view incidents/analytics/reports. Only **Admin** can manage zones
(add/update/remove) and register new users — enforced both in the UI
(routes) and the API (`require_admin`).

**Q: Where is evidence stored?**
A: Local directory `evidence/` — one `.jpg` per incident with bounding boxes
drawn on it, filename encodes zone/type/timestamp. Served read-only via
`GET /api/evidence/{file}` (officer role required).

**Q: How is the PDF report generated?**
A: `GET /api/reports/pdf` (optional date/zone filters) → SQLAlchemy
aggregates incidents → `fpdf2` builds a formatted PDF (title, generation
time, filters, summary counts, by-zone breakdown, incident table up to 500
rows) into `reports/`, returned as a file download.

## Project management questions

**Q: What did each member do?** (suggestion — rearrange as true)
A: Mohsin — AI model, dataset pipeline, training & evaluation. Usman —
FastAPI backend, auth/RBAC, MySQL schema. Hamza — React frontend, dashboard,
charts, alerts UI.

**Q: What are the limitations?**
A: (1) CPU validation model is not production-accurate — needs the GPU run.
(2) Small smoking class (557 images) until the Roboflow set is merged.
(3) Single-camera video-file processing; multi-RTSP scaling is future work.
(4) No identity recognition — detects *objects/behaviors*, not *who*.

**Q: Future work?**
A: Temporal smoothing across frames, multi-camera RTSP support, vaping-specific
class (vape devices vs cigarettes), ONNX/OpenVINO export for edge deployment,
 SMS/email escalation for critical zones, larger merged dataset training.
