# Restricted Zone Contraband Detection System
## Real-Time Multi-Class Violation Detection using YOLOv11, FastAPI, React.js and MySQL

**Final Year Project Report — BS Software Engineering**
**The University of Lahore, Faculty of Information Technology**

| Student ID | Name | Suggested responsibility |
|---|---|---|
| 70148217 | Muhammad Mohsin | AI model · dataset · training & evaluation |
| 70144882 | Usman Siddique | FastAPI backend · MySQL |
| 70138335 | Hamza Habib Khan | React.js frontend · dashboard |

> The responsibility split above is a suggestion; the team may rearrange it.
> Supervisor: ____________________  Date: ______________

---

## Abstract

Manual CCTV surveillance in restricted zones — server rooms, petrol pumps,
examination halls — depends on human operators watching screens for hours.
Fatigue and oversight cause delayed or missed responses to critical
violations such as unauthorized mobile phone usage and smoking/vaping, which
create data-security, fire-safety and academic-integrity risks. This project
presents an automated, software-only contraband detection system that runs on
existing camera infrastructure with no hardware modifications. A
custom-trained **YOLOv11** object-detection model processes video streams and
simultaneously detects two violation classes — `smoking` and `mobile_phone`.
A **Python FastAPI** backend orchestrates detection, automatically logs every
incident (timestamp, violation type, zone, confidence) with an evidence frame
snapshot into a **MySQL** database, and pushes instant red-toast alerts over
WebSocket to a role-based **React.js** dashboard (Admin / Security Officer).
The dashboard provides zone management, a runtime confidence-threshold
slider, incident search/filter, analytics charts, and one-click PDF
compliance reports. The model was trained by transfer learning on a merged,
verified dataset: the published **CigDet** cigarette dataset (Mendeley, DOI
10.17632/6hyrr8typ7.1) and a **COCO 2017** `cell phone` subset. The system
meets its <2 s frame-to-alert latency target and degrades gracefully on
corrupt streams.

**Keywords:** YOLOv11, object detection, contraband detection, FastAPI,
React.js, MySQL, intelligent surveillance, restricted zones.

---

## 1. Introduction

Closed-circuit television is the backbone of physical security, yet in most
installations cameras are passive recorders. A human operator must notice a
violation the moment it happens — an expectation that collapses under
fatigue, divided attention across many screens, and shift work. In
restricted zones the cost of a missed event is severe: a phone in a server
room can exfiltrate data; a cigarette at a petrol pump can ignite fuel
vapor; a phone in an examination hall enables cheating.

Existing commercial answers are unsatisfactory for most organizations.
Hardware-AI cameras (e.g., Hikvision smart cameras) demand expensive
proprietary hardware overhauls. Consumer cloud cameras (e.g., Google Nest)
charge subscriptions, detect only generic activity, and keep data off-site.
Ticketing platforms (Freshdesk/Zendesk) log compliance manually with no
computer-vision trigger at all.

This project bridges the gap with a **software-only, hardware-agnostic**
pipeline: any existing video feed → YOLOv11 multi-class detection →
automatic database audit log + evidence snapshot → instant visual alert →
analytics and compliance reporting. The deep-learning core (YOLOv11,
transfer-learned on a curated two-class dataset) is wrapped in an
enterprise-style full-stack application (FastAPI + React + MySQL) with
role-based access control, satisfying both the AI and software-engineering
dimensions of the degree.

## 2. Problem Statement

Traditional CCTV surveillance relies on passive manual monitoring, leading
to human fatigue, oversight, and delayed responses in security compliance.
Current workflows lack an automated system to simultaneously detect
multi-class violations — unauthorized mobile phone usage and smoking/vaping
— within restricted zones like server rooms, petrol pumps, or examination
halls, and to instantly log temporal-spatial incident data for governance
with immediate visual alerting, without expensive hardware modifications.

## 3. Objectives

1. Develop a secure, user-friendly, multi-role contraband detection web
   application for restricted-area surveillance and compliance management.
2. Train and deploy a high-accuracy YOLOv11 model that simultaneously
   detects mobile phone usage and smoking/vaping in video streams.
3. Engineer a responsive React.js dashboard for monitoring, alerting and
   administration.
4. Trigger instant visual (red toast) alerts the moment a violation is found.
5. Automatically log incidents (timestamp, violation type, zone) with
   evidence snapshots into a centralized MySQL database via FastAPI.
6. Provide trend analytics (bar/pie charts) and one-click PDF compliance
   reports.

## 4. Scope

**In scope:** two violation classes (`smoking`, `mobile_phone`); video-file
input tagged to a configured camera zone; real-time detection loop;
RBAC (Admin/Security Officer); zone CRUD; confidence-threshold tuning;
incident logging + evidence archiving; analytics; filtered search; PDF
reports; local deployment on commodity hardware.
**Out of scope:** facial/person identification, multi-camera RTSP fleets,
vape-vs-cigarette fine-grained distinction, mobile-app client, cloud hosting.

## 5. Literature Review

Object detection evolved from handcrafted features (HOG + SVM, Dalal &
Triggs) to two-stage deep networks (Faster R-CNN, Ren et al., 2015), which
are accurate but slow due to the region-proposal stage. Redmon et al.
(2016) introduced **YOLO (You Only Look Once)**, reframing detection as a
single regression problem: one network pass predicts bounding boxes and
class probabilities directly, enabling real-time speeds. The Ultralytics
YOLO lineage (v5 → v8 → v11) progressively improved the backbone/neck
(CSPDarknet → C2f → C3k2), loss formulation, and small-object performance.
YOLOv11 (Ultralytics, 2024) is the current state of the art in this family
and the basis of this project; its documentation is at
https://docs.ultralytics.com.

For the smoking class we use **CigDet** (Ali Khan, Mendeley Data, 2024,
DOI 10.17632/6hyrr8typ7.1): 557 YOLO-annotated cigarette images across
diverse scenes. For mobile phones we use the **COCO 2017** `cell phone`
class (Lin et al., ECCV 2014), the standard large-scale detection
benchmark. A related Roboflow "Smoking Dataset" (2,337 images;
face/cigarette/smoker) cited in recent smoking-behavior studies is
documented as the recommended extension for the production training run.

## 6. Dataset

| Aspect | Class `0` — smoking | Class `1` — mobile_phone |
|---|---|---|
| Source | CigDet, Mendeley Data | COCO 2017 |
| Link | https://data.mendeley.com/datasets/6hyrr8typ7/1 | http://images.cocodataset.org/annotations/annotations_trainval2017.zip |
| Identifier | DOI 10.17632/6hyrr8typ7.1 | category_id 67 ("cell phone") |
| Raw size | 557 images (446 train / 111 test) | ≤ 400 images (cell-phone subset) |
| Annotation | YOLO `.txt`, LabelImg | COCO JSON → converted to YOLO |
| Verification | SHA-256 `ef2ab181…936bae41` matched | parsed from official annotations |

The merge script (`ai/dataset/prepare_yolo_dataset.py`) produces
`ai/dataset/yolo/` in Ultralytics format (`images/train|val`,
`labels/train|val`, `data.yaml` with `names: {0: smoking, 1: mobile_phone}`).
CigDet's train split → our train, its test split → our val; COCO phones are
split 80/20. Full dataset cards: `docs/DATASETS.md`.

## 7. Methodology

1. **Data acquisition & verification** — download from verified links only;
   hash-check binaries; inspect label formats.
2. **Preprocessing** — YOLO normalization check; COCO `[x,y,w,h]` →
   normalized `(x_center, y_center, w, h)`; degenerate boxes dropped.
3. **Model** — YOLOv11 nano, transfer learning from COCO-pretrained weights.
4. **Training** — CPU validation run (this report) + documented GPU recipe.
5. **Integration** — weights loaded once by the FastAPI backend; frame loop
   with configurable stride; threshold filtering; incident persistence.
6. **Evaluation** — precision, recall, mAP50, mAP50-95 on the val split;
   latency measured per frame.

## 8. System Architecture

```
┌─────────────────┐      REST / WS       ┌──────────────────┐     infer      ┌──────────────────┐
│  React.js       │◄────────────────────►│  FastAPI backend  │◄──────────────►│  YOLOv11 engine  │
│  Admin/Officer  │                      │  auth·RBAC·zones  │                │  smoking / phone │
│  upload·slider  │                      │  detect loop·PDF  │                └──────────────────┘
│  red-toast alert │                      └────────┬─────────┘
└─────────────────┘                               │ SQLAlchemy
                                         ┌────────▼─────────┐      .jpg/.pdf     ┌──────────────────┐
                                         │  MySQL (SQLite   │◄──────────────────►│  Local storage   │
                                         │  for local dev)  │                    │  evidence/reports  │
                                         └──────────────────┘                    └──────────────────┘
```

A detailed SVG diagram is in `docs/architecture.svg`. Data flow: officer
uploads a video and selects the camera zone → backend runs the YOLOv11
frame loop → each detection above threshold creates an incident row
(timestamp, type, zone, confidence) + an evidence `.jpg` → a WebSocket event
fires a red toast on the dashboard instantly → analytics aggregates the DB
into charts → one click exports the PDF compliance report.

**Component responsibilities:**
- *Frontend (React.js):* login, live monitor (upload + zone dropdown +
  threshold slider), zones admin, incident search, analytics charts, reports.
- *Backend (FastAPI):* JWT auth with bcrypt-hashed passwords, RBAC guards,
  zone CRUD, video handling, detection orchestration, incident logging,
  analytics aggregation, PDF generation, WebSocket alert bus.
- *AI engine:* custom YOLOv11 weights (`ai/runs/best.pt`), 2-class
  inference with per-frame latency tracking.
- *Database:* `users`, `zones`, `incidents`, `settings` tables.
- *Storage:* `evidence/` snapshots, `reports/` PDFs, `backend/uploads/`
  videos.

## 9. Model Details — YOLOv11

YOLOv11 (Ultralytics, 2024) is a single-stage detector: backbone (feature
extraction with C3k2 blocks) → neck (multi-scale feature fusion, PAN-style)
→ anchor-free decoupled head predicting box coordinates, objectness and
class scores per grid cell, filtered by non-maximum suppression. The nano
variant (`yolo11n`, ~2.6 M parameters) was chosen for CPU-friendly
inference, satisfying the low-hardware-dependency requirement. Training
uses transfer learning: COCO-pretrained weights are fine-tuned on the
two-class dataset (see §10).

## 10. Training Details

| Hyperparameter | CPU validation run (this report) | Full GPU recipe (Colab) |
|---|---|---|
| Model | yolo11n (COCO-pretrained) | yolo11n / yolo11s |
| Epochs | 3 | 100 |
| Image size | 320 | 640 |
| Batch | 8 | 16 |
| Device | CPU (2 cores) | T4 GPU |
| Optimizer | AdamW, lr0=0.001 | AdamW, lr0=0.001, cosine lrf=0.01 |
| Workers | 1 | 8 |
| Patience (early stop) | 20 | 25 |
| Augmentation | YOLO defaults (mosaic, HSV, flip, scale) | same + tuned schedule |

**Measured results — CPU validation run (real, 2026-10-18):**
transfer learning from COCO-pretrained `yolo11n.pt`, 766 training
images / 191 validation images, ~20.5 min on a shared 2-CPU VM.
Exported `ai/runs/best.pt` (5.5 MB). Source:
`runs/detect/yolo11n_contraband_cpu/results.csv` + final validation.

| Metric | Epoch 1 | Epoch 2 | Epoch 3 (final) |
|---|---|---|---|
| train box / cls / dfl loss | 2.119 / 2.654 / 1.760 | 2.005 / 2.252 / 1.698 | 1.943 / 2.062 / 1.662 |
| Precision (all classes) | 0.374 | 0.531 | 0.486 |
| Recall (all classes) | 0.250 | 0.352 | 0.439 |
| mAP50 | 0.236 | 0.329 | 0.366 |
| mAP50-95 | 0.099 | 0.142 | 0.187 |
| Training time (cumulative) | 7.4 min | 13.9 min | 20.4 min |

Per-class validation of `best.pt` (191 images, 228 instances):

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| smoking | 111 | 111 | 0.493 | 0.562 | 0.419 | 0.191 |
| mobile_phone | 80 | 117 | 0.478 | 0.316 | 0.313 | 0.184 |

Inference speed (CPU): 1.6 ms preprocess + 86.8 ms inference +
2.7 ms postprocess per image — comfortably inside the
<2 s frame-to-alert non-functional requirement.

**Scope honesty:** the 3-epoch CPU run validates the pipeline end-to-end
(data loads correctly, loss decreases, metrics compute, weights export).
Production accuracy requires the GPU recipe
(`ai/full_training_recipe_COLAB.md`).

## 11. Libraries & Technologies

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| AI | ultralytics | 8.182 | YOLOv11 training & inference |
| AI | torch / torchvision (CPU) | 2.14.1 / 0.29.1 | deep-learning backend |
| AI | opencv-python-headless | 5.3 | frame capture, evidence annotation |
| Backend | fastapi | 0.144.0 | async REST API + WebSocket |
| Backend | uvicorn | 0.54.0 | ASGI server |
| Backend | sqlalchemy | 2.5 | ORM (SQLite dev / MySQL prod) |
| Backend | pymysql | 1.3 | MySQL driver |
| Backend | python-jose / bcrypt | 3.0 / 5.0 | JWT auth, password hashing (bcrypt used directly) |
| Backend | fpdf2 | 2.9 | PDF compliance reports |
| Frontend | react / react-dom | 18.1 | UI |
| Frontend | vite | 5.0 | build tooling |
| Frontend | react-router-dom | 6.23.0 | routing + role guards |
| Frontend | axios | 1.0 | API calls (ES6+) |
| Frontend | recharts | 2.12.0 | bar/pie analytics charts |
| Frontend | react-hot-toast | 2.1 | red violation toasts |
| Data | pandas / matplotlib / pyyaml | 3.6 / 3.11.2 / 6.3 | prep & analysis |
| DB (prod) | MySQL | 8.0 (docker) | production database |
| Tools | VS Code, Postman, Git | — | dev / API testing / VCS |

## 12. Results & Evaluation

- **Pipeline:** video upload → detection → DB logging → evidence snapshot →
  WebSocket alert → analytics → PDF report, all verified working against the
  FastAPI backend (see `postman/contraband_api_collection.json` for the
  tested request set).
- **Detection metrics:** see §10 table (real numbers from the CPU run).
- **End-to-end test with the trained model (2026-10-18):** a 15-frame test
  video built from a real validation image was uploaded
  (`POST /api/videos/upload`), then run through detection
  (`POST /api/detect/run`, zone = Server Room, threshold 0.25):
  **5/5 frames processed, 5 smoking incidents created** (confidence
  ≈ 0.50), **5 evidence .jpg snapshots saved to `evidence/`** (20–21 KB
  each), all rows present in the incidents table with timestamps and zone
  names, `/api/analytics/summary` aggregating correctly, and the PDF
  compliance report downloading (HTTP 200).
- **Latency:** per-frame inference latency is measured and returned with
  every detection. First call after load ≈ 9 s (one-time warmup); steady
  state on this shared 2-CPU VM is **137–310 ms/frame**, inside the <2 s
  frame-to-alert budget.
- **Robustness:** corrupt/unsupported videos return HTTP 400; per-frame
  exceptions are isolated; the DB connection uses `pool_pre_ping`.

## 13. Limitations

1. The CPU validation model is not production-accurate; the GPU run is required.
2. The smoking class is small (557 images) until the Roboflow set is merged.
3. Video-file input only in this build; multi-camera RTSP is future work.
4. Detects objects/behaviors, not identities; no tracking across frames yet.
5. Vaping devices are covered under the `smoking` class (no fine-grained split).

## 14. Future Work

Temporal smoothing (detection must persist N frames), multi-RTSP camera
support, dedicated `vaping` class, ONNX/OpenVINO export for edge servers,
SMS/email escalation for critical zones, and full-dataset GPU training with
hyperparameter search.

## 15. References

1. Ultralytics. "YOLOv11 Real-Time Object Detection Framework Overview."
   https://docs.ultralytics.com
2. FastAPI. "Asynchronous Web Framework for Python Architecture and Production
   Routing." https://fastapi.tiangolo.com
3. React Documentation. "Interactive Component-Based UI Development for
   Enterprise Web Portals." https://react.dev
4. Oracle MySQL. "Relational Database Management Systems and Structured Query
   Architecture." https://www.mysql.com
5. Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. "You Only Look Once:
   Unified, Real-Time Object Detection." IEEE CVPR, 2016.
6. Ali Khan. "CigDet (Cigarette Detection) Dataset." Mendeley Data, 2024.
   DOI 10.17632/6hyrr8typ7.1. https://data.mendeley.com/datasets/6hyrr8typ7/1
7. Lin, T.-Y., et al. "Microsoft COCO: Common Objects in Context." ECCV, 2014.
   https://cocodataset.org

---

## Appendix A — API endpoint map (all 11 functional requirements)

See README.md. A Postman-tested collection is in
`postman/contraband_api_collection.json`.

## Appendix B — Screenshots

*(Capture during the demo: Login, Live Monitor with red toast alert,
Zones admin, Incidents filter, Analytics charts, PDF report.)*

- Fig. B1 — Login page: `docs/screenshots/01_login.png`
- Fig. B2 — Live monitor + red violation toast: `docs/screenshots/02_dashboard_alert.png`
- Fig. B3 — Analytics dashboard: `docs/screenshots/03_analytics.png`
