# BUILD LOG — A-to-Z (Restricted Zone Contraband Detection System)

Everything done to build this project, in order, with every command, every
decision and WHY. Written 2026-10-18 by the build agent for Muhammad Mohsin
(70148217), Usman Siddique (70144882), Hamza Habib Khan (70138335).

> Suggested split (rearrange freely): **Mohsin** — AI model/dataset/training;
> **Usman** — FastAPI backend + MySQL; **Hamza** — React frontend + dashboard.

---

## 0. Starting point

- Read the approved proposal `~/workspace/user/files/FORM-1_Project_Proposal_Form.pdf`
  in full. Non-negotiables extracted: YOLOv11 multi-class (mobile phones +
  smoking/vaping), Python FastAPI async backend, React.js frontend with
  Admin + Security Officer roles, MySQL, local storage for evidence `.jpg`
  and PDF reports, tools Python / JS ES6+ / Axios / Postman / VS Code.
- All 11 functional requirements + 4 non-functional requirements mapped to
  API endpoints (see README.md table).
- Work directory: `~/workspace/fyp-cigarette-detection/`.

## 1. Environment

- Machine: Linux VM, Python 3.12.3, 2 CPUs, ~7 GB RAM (shared with a video
  worker, so CPU threads were capped everywhere).
- `python3 -m venv .venv` — virtualenv keeps project deps isolated from the
  system Python (system pip is PEP-668 protected; the venv avoids that).
- Installed CPU-only PyTorch first (no NVIDIA GPU on this VM):
  `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`
  (torchvision download kept timing out and retrying; torch itself landed fine,
  the rest of the install completed and torchvision eventually arrived too).
- Then: `ultralytics opencv-python-headless fastapi "uvicorn[standard]"
  sqlalchemy pymysql "python-jose[cryptography]" "passlib[bcrypt]" fpdf2
  python-multipart numpy pillow pandas matplotlib pyyaml tqdm requests awscli`
- Full list with pinned versions: `requirements.txt` (generated from `pip freeze`).
- Node v24 + npm were already on the machine → React frontend builds fine.
- No MySQL server on the VM and only ~1 GB free RAM → MySQL install skipped
  **for local validation**; the backend uses SQLAlchemy with `DATABASE_URL`,
  defaulting to SQLite (`fyp.db`) locally and MySQL (`mysql+pymysql://…`)
  in production. Same tables, same code, one env var switches. Production
  MySQL is provided via `docker-compose.yml` (mysql:8.0 + phpMyAdmin).

## 2. Dataset research (every link verified — nothing invented)

1. Searched Roboflow Universe / papers for smoking datasets → found a JAIEA
   paper citing a Roboflow "Smoking Dataset" (2,337 images, classes
   face/cigarette/smoker). Roboflow downloads need a **free API key**
   (**human step**: sign up at roboflow.com → Settings → API key). Kept as
   the recommended source for the FULL training run (documented in
   `docs/DATASETS.md` §3 with exact code).
2. Searched HuggingFace Hub API (`ccclllwww/smoker_img_detection`,
   `ccclllwww/smoking_img_final`, …) → classification folders only, **no
   bounding boxes** → rejected for detection training (documented).
3. Checked Open Images V5 `class-descriptions-boxable.csv` (601 classes,
   downloaded from the official GCS bucket) → **no cigarette/smoking class
   exists** → rejected (documented).
4. Found **CigDet (Cigarette Detection) Dataset**, Mendeley Data,
   DOI 10.17632/6hyrr8typ7.1, 557 YOLO-annotated images. Verified the file
   list via the Mendeley public API, downloaded
   `CigDet_dataset.zip` (34,689,636 bytes) and **verified SHA-256
   `ef2ab181…936bae41` matched** before use. (First attempt broke at
   29.5 MB — flaky network — retried with HTTP Range resume.)
5. **COCO 2017** for the `mobile_phone` class: `category_id 67`
   ("cell phone"). Downloaded `annotations_trainval2017.zip` (241 MB) from
   `http://images.cocodataset.org/annotations/`, parsed the JSON, kept
   images containing cell phones (cap 400), downloaded each via its
   `coco_url`, converted `[x,y,w,h]` to YOLO normalized as class 1.
6. Merge script `ai/dataset/prepare_yolo_dataset.py`:
   CigDet train→train / test→val as class `0` (smoking); COCO phones 80/20
   as class `1` (mobile_phone). Output `ai/dataset/yolo/` + `data.yaml`
   (`names: {0: smoking, 1: mobile_phone}`).

**How components connect (data flow):**
dataset scripts → `ai/dataset/yolo/` (images+labels, YOLO format) →
`ai/train.py` (YOLOv11 transfer learning) → `ai/runs/best.pt` →
`backend/detector.py` (loads weights once) → `/api/detect/run` frame loop →
incidents in MySQL/SQLite + evidence `.jpg` → WebSocket red-toast alerts →
React dashboard / analytics / PDF report.

## 3. Model training

- Model: **YOLOv11 nano** (`yolo11n.pt`, ~5 MB COCO-pretrained) via
  `ultralytics==8.182`. Transfer learning: COCO backbone weights +
  fine-tune on our 2-class dataset.
- Validation run on this VM (CPU, 2 cores, RAM-limited):
  `python ai/train.py --epochs 3 --imgsz 320 --batch 8`
  (workers=1, AdamW, lr0=0.001, patience=20). Threads capped at 2 with
  `torch.set_num_threads()` so the video worker on the same machine is
  not starved. (First attempt: 5 epochs @416px with 1 thread proved too
  slow under ffmpeg contention — restarted leaner; still a full
  end-to-end validation on all 766 training images.)
- Outputs: `runs/detect/<name>/` (weights, `results.csv`, training plots)
  → `best.pt` copied to `ai/runs/best.pt` for the backend (`MODEL_PATH`).
- **Honest scope**: 3 epochs on CPU only *validates the pipeline*
  end-to-end (data loads, loss decreases, mAP is computed). It is NOT a
  production model. Real numbers are in `docs/FYP_Report.md` §Training.
- **Result (2026-10-18, completed):** 3 epochs in 20.4 min;
  mAP50 0.236 → 0.329 → **0.366**; per-class mAP50 smoking 0.419 /
  mobile_phone 0.313; `ai/runs/best.pt` (5.5 MB). Backend E2E with this
  model: 5/5 frames detected (smoking ≈ 0.50), 5 incidents + 5 evidence
  .jpgs, analytics + PDF verified. Steady-state inference 137–310 ms/frame
  (9 s one-time warmup) — inside the <2 s frame-to-alert budget.
- Production recipe: `ai/full_training_recipe_COLAB.md` — Colab T4 GPU,
  100 epochs, imgsz 640, batch 16, full augmentation schedule, early
  stopping, then `model.val()` + ONNX/OpenVINO export.

## 4. Backend — FastAPI (`backend/`)

- `app_config.py` — central config loader: reads `config/settings.yaml`
  (model path, DB URL, dirs, JWT secret, defaults); `FYP_*` env vars
  override it (legacy bare names like `DATABASE_URL` also work).
- `database.py` — SQLAlchemy engine from `DATABASE_URL` (SQLite dev /
  MySQL prod), session dependency, `init_db()`.
- `models.py` — `User` (username unique, bcrypt `password_hash`, role
  admin|officer), `Zone` (name unique, description), `Incident`
  (timestamp, violation_type, zone_id FK, confidence, camera_location,
  evidence_path), `Setting` (key/value, holds the confidence threshold).
- `auth.py` — `passlib` bcrypt hashing, `python-jose` JWT
  (`HS256`, configurable secret/expiry), `OAuth2PasswordBearer`,
  `get_current_user`, `require_admin`, `require_officer` (RBAC guards).
- `detector.py` — `YOLODetector` loads `best.pt` once (singleton),
  `infer_frame()` returns detections + per-frame latency ms,
  `draw()` annotates evidence frames. Classes: 0=smoking, 1=mobile_phone.
- `main.py` — all 11 FRs as REST endpoints + `WS /ws/alerts`:
  FR1 `/api/auth/*`, FR2 `/api/zones` CRUD (admin-only writes),
  FR3 `/api/settings/threshold`, FR4 `/api/videos/upload` (mp4/avi/mov/mkv/webm),
  FR5 `/api/detect/run` (frame loop with `frame_skip`, per-frame try/except
  so one bad frame never kills the loop; corrupt video → clean 400, never a
  crash), FR6 WebSocket broadcast → red toast, FR7 incident INSERT per
  detection, FR8 `cv2.imwrite` evidence `.jpg` per incident,
  FR9 `/api/analytics/summary` (by type/zone/day), FR10 `/api/incidents`
  (date/zone/type filters), FR11 `/api/reports/pdf` (fpdf2).
- `reports.py` — `ComplianceReport` (fpdf2): header, summary counts,
  by-zone table, incident log table (capped 500 rows), page numbers.
- `seed.py` — creates `admin/admin123` + zones (Server Room, Petrol Pump,
  Examination Hall). Run once: `python -m backend.seed`.
- Non-functional: frame-to-alert < 2 s target — yolo11n on CPU does
  ~80–200 ms/frame at 640px, WebSocket push is ~ms; measured latency is
  logged per detection and shown in the toast payload.

## 5. Frontend — React.js (`frontend/`)

- Vite 5 + React 18 + react-router-dom + axios + recharts + react-hot-toast.
- `src/api/client.js` — axios instance, JWT from localStorage, 401 → logout.
- Pages: `Login` (form-encoded OAuth2 login), `Dashboard` (FR4 upload +
  zone dropdown, FR3 threshold slider, FR5 run button, live table, FR6
  WebSocket → red toast), `Zones` (FR2 admin CRUD), `Incidents` (FR10
  search/filter), `Analytics` (FR9 pie + bar charts from DB aggregates),
  `Reports` (FR11 one-click PDF download).
- `App.jsx` — role-based routes (`/zones` admin-only), dark responsive CSS
  (`index.css`, grid collapses to 1 column on mobile — NFR responsive UI).
- Dev proxy: `/api` and `/ws` → `localhost:8000` (vite.config.js).

## 6. Extras (beyond the proposal — all safe additions)

- `postman/contraband_api_collection.json` — importable Postman collection,
  every endpoint, login test auto-saves the JWT to a collection variable.
- `docs/architecture.svg` — hand-drawn system architecture + data-flow diagram.
- `docker-compose.yml` — MySQL 8.0 + phpMyAdmin for the production DB setup
  (the proposal names Workbench/phpMyAdmin as tooling).
- `.env.example` — every config knob documented (DB URL, JWT secret,
  MODEL_PATH, thresholds, storage dirs).
- `ai/dataset/*.py` — reproducible download/verify/prepare scripts with
  SHA-256 checks and resume support (not just "download from Kaggle").
- `backend/uploads/`, `evidence/`, `reports/` runtime dirs with `.gitkeep`.

## 7. Debugging & verification (real issues hit and fixed)

1. **PEP 668**: system pip refused installs → used a project venv
   (`.venv/`) for everything.
2. **torchvision wheel timeouts** on download.pytorch.org → retried; torch
   CPU landed, install completed.
3. **passlib 1.4 + bcrypt 5.0 incompatibility** (`password cannot be longer
   than 72 bytes` crash in `backend/seed.py`): root cause is passlib's
   unmaintained bcrypt handler vs modern bcrypt. **Fix**: dropped passlib,
   `backend/auth.py` now uses the `bcrypt` library directly
   (`hashpw`/`checkpw`, 72-byte truncation), `requirements.txt` updated.
4. **Pydantic v2 `from_orm` deprecation** in `/api/incidents` → switched to
   `model_validate`.
5. **Missing model weights** on `/api/detect/run` → now returns clean
   HTTP 503 with an actionable message instead of a 500 crash.
6. **API tests (all passing, 2026-10-18)**: health 200; admin login 200;
   zones list (3 seeded); threshold get/set; analytics empty-summary;
   officer registration 201; officer DELETE zone → 403 (RBAC enforced);
   wrong password → 401; video upload 200; PDF report 200
   (`application/pdf`); frontend `npm run build` succeeded.
7. **CigDet download** broke at 29.5/34.7 MB → resumed via HTTP Range,
   SHA-256 verified.

## 8. Human / approval steps the team must do themselves

- **Roboflow API key** (free): sign up at roboflow.com → Settings → API key,
  needed only for the extended smoking dataset in the full GPU run
  (`docs/DATASETS.md` §3). Nothing else in this project needs an account.
- **MySQL production**: `docker compose up -d`, create `.env` from
  `.env.example` with `DATABASE_URL=mysql+pymysql://…` and a strong
  `JWT_SECRET`; change `admin/admin123` after first login.
- **GPU training**: run `ai/full_training_recipe_COLAB.md` on Colab (T4),
  copy the resulting `best.pt` to `ai/runs/best.pt`.
- **Demo screenshots**: capture the UI and drop into
  `docs/screenshots/` (Appendix B of the report references them).
