# Restricted Zone Contraband Detection System

**Final Year Project — BS Software Engineering, The University of Lahore**
Team: Muhammad Mohsin (70148217) · Usman Siddique (70144882) · Hamza Habib Khan (70138335)

Automated, AI-driven surveillance: a custom-trained **YOLOv11** model detects
**smoking/vaping** and **mobile phone usage** in restricted zones (server rooms,
petrol pumps, examination halls). A **FastAPI** backend logs every incident to
**MySQL** with an evidence snapshot, and a **React.js** dashboard gives security
staff live red-toast alerts, analytics charts, and one-click PDF compliance reports.

Suggested responsibility split (rearrange freely):
- **Muhammad Mohsin** — AI model: dataset, training, evaluation
- **Usman Siddique** — FastAPI backend + MySQL
- **Hamza Habib Khan** — React frontend + dashboard

## One-command setup

```bash
# 1. Python environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Database (SQLite by default; MySQL via docker for production)
#    SQLite: nothing to do.  MySQL: docker compose up -d
#    then set DATABASE_URL in .env (see .env.example)

# 3. Seed admin user + default zones
python -m backend.seed          # admin / admin123  (change after login!)

# 4. Train (or download) the model -> ai/runs/best.pt
python ai/dataset/download_cigdet.py
python ai/dataset/download_coco_phones.py
python ai/dataset/prepare_yolo_dataset.py
python ai/train.py --epochs 3 --imgsz 320 --batch 8

# 5. (Optional) edit config/settings.yaml — model path, DB URL, dirs, JWT secret.
#    Environment variables override it: FYP_DATABASE_URL, FYP_MODEL_PATH, FYP_JWT_SECRET, ...

# 6. Run backend
uvicorn backend.main:app --reload --port 8000

# 7. Run frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## Project layout

```
backend/        FastAPI app (auth/RBAC, zones, detection loop, incidents, analytics, PDF)
frontend/       React.js + Vite dashboard (login, live monitor, zones, incidents, analytics, reports)
ai/             dataset scripts, YOLOv11 training, Colab GPU recipe, runs/
config/         settings.yaml — central config (backend/app_config.py loads it)
docs/           BUILD_LOG_AtoZ.md, FYP_Report.md, VIVA_PREP.md, DATASETS.md, architecture.svg
postman/        Postman-tested API collection (import into Postman)
evidence/       violation frame snapshots (.jpg) — created at runtime
reports/        generated compliance PDFs — created at runtime
```

## API quick map (all 11 functional requirements)

| # | Requirement | Endpoint |
|---|-------------|----------|
| 1 | Auth + RBAC, hashed passwords | `POST /api/auth/login`, `/api/auth/register` (admin), `/api/auth/me` |
| 2 | Zone add/update/remove | `GET/POST /api/zones`, `PUT/DELETE /api/zones/{id}` (admin) |
| 3 | Confidence-threshold slider | `GET/POST /api/settings/threshold` |
| 4 | Video upload + camera dropdown | `POST /api/videos/upload` |
| 5 | YOLOv11 multi-class detection loop | `POST /api/detect/run` |
| 6 | Instant red toast alerts | `WS /ws/alerts` |
| 7 | Auto incident logging (MySQL) | inside `/api/detect/run` |
| 8 | Evidence frame snapshot | saved to `evidence/`, `GET /api/evidence/{file}` |
| 9 | Analytics (bar + pie) | `GET /api/analytics/summary` |
| 10 | Search/filter incidents | `GET /api/incidents?date_from&date_to&zone_id&violation_type` |
| 11 | PDF compliance report | `GET /api/reports/pdf` |

## Docs

- [docs/BUILD_LOG_AtoZ.md](docs/BUILD_LOG_AtoZ.md) — every step, every command, every decision
- [docs/FYP_Report.md](docs/FYP_Report.md) — full professional project report
- [docs/VIVA_PREP.md](docs/VIVA_PREP.md) — viva questions + answers
- [docs/DATASETS.md](docs/DATASETS.md) — dataset cards with verified links
- [docs/architecture.svg](docs/architecture.svg) — system architecture diagram
- [ai/full_training_recipe_COLAB.md](ai/full_training_recipe_COLAB.md) — GPU training recipe
