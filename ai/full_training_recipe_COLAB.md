# Full Training Recipe — YOLOv11 on GPU (Google Colab)

Use this to train the **production-quality** model. The CPU run in
`ai/train.py` only validates the pipeline end-to-end; real accuracy needs
GPU training with more epochs on the full dataset.

## 1. Open a Colab GPU runtime
- https://colab.research.google.com → Runtime → Change runtime type → **T4 GPU**.

## 2. Setup (one cell)
```bash
pip install ultralytics
```

## 3. Upload the dataset
Upload `ai/dataset/yolo/` (images/train, images/val, labels/train,
labels/val, data.yaml) to Colab, e.g. `/content/yolo/`, and point
`data.yaml`'s `path:` at it. For the full dataset also add the Roboflow
"Smoking Dataset" (2,337 images, classes face/cigarette/smoker) —
see `docs/DATASETS.md` for the exact download snippet (needs a free
Roboflow API key).

## 4. Train (one cell)
```python
from ultralytics import YOLO
model = YOLO("yolo11n.pt")          # or yolo11s.pt for higher accuracy
model.train(
    data="/content/yolo/data.yaml",
    epochs=100,                     # full schedule (CPU validation used 5)
    imgsz=640,                      # full resolution (CPU validation used 416)
    batch=16,                       # T4-safe; use 32 on A100/L4
    device=0,
    pretrained=True,                # transfer learning from COCO weights
    optimizer="AdamW",
    lr0=0.001,
    lrf=0.01,                       # final lr = lr0 * lrf (cosine schedule)
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3,
    patience=25,                    # early stopping
    # --- augmentation (YOLOv11 defaults, tuned for small objects) ---
    hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
    degrees=0.0, translate=0.1, scale=0.5,
    fliplr=0.5, mosaic=1.0, mixup=0.0,
    copy_paste=0.0,
    save=True, plots=True, val=True,
    name="yolo11n_contraband_full",
)
```

## 5. Evaluate
```python
metrics = model.val()   # mAP50, mAP50-95, precision, recall per class
print(metrics.box.map, metrics.box.map50, metrics.box.mp, metrics.box.mr)
```

## 6. Export for deployment
```python
model.export(format="onnx")   # or format="openvino" for Intel CPU servers
```
Copy the resulting `best.pt` (or `.onnx`) to the project's `ai/runs/`
folder and set `MODEL_PATH` in the backend environment.

## Suggested experiment log (fill in as you train)

| Run | Model | Epochs | imgsz | batch | mAP50 | mAP50-95 | Notes |
|-----|-------|--------|-------|-------|-------|----------|-------|
| CPU validation | yolo11n | 3 | 320 | 8 | *see FYP_Report* | | pipeline validation only |
| Full #1 | yolo11n | 100 | 640 | 16 | | | |
| Full #2 | yolo11s | 100 | 640 | 16 | | | if T4 memory allows |
