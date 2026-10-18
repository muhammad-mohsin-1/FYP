"""YOLOv11 detection engine.

Loads the custom-trained YOLOv11 weights once at startup and exposes a
frame-level inference API used by the video detection loop in main.py.

The model detects two classes (see ai/dataset/data.yaml):
    0 -> smoking        (cigarettes / vaping devices)
    1 -> mobile_phone   (unauthorized phone usage)

Frame-to-alert latency target: < 2 s (non-functional requirement).
On CPU (yolo11n, imgsz 640) a single frame typically takes 80-200 ms,
so the budget is met comfortably even with frame skipping disabled.
"""
import os
import time
import cv2
import numpy as np

from . import app_config

MODEL_PATH = app_config.MODEL_PATH
DEFAULT_CONF = app_config.DEFAULT_CONF

CLASS_NAMES = {0: "smoking", 1: "mobile_phone"}


class YOLODetector:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self._load()

    def _load(self):
        from ultralytics import YOLO
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model weights not found at {self.model_path}. "
                "Train the model first (see ai/train.py) or set MODEL_PATH."
            )
        self.model = YOLO(self.model_path)

    def infer_frame(self, frame: np.ndarray, conf: float = DEFAULT_CONF):
        """Run detection on a single BGR frame. Returns (detections, latency_ms).

        detections: list of dicts {class_id, class_name, confidence, bbox[x1,y1,x2,y2]}
        """
        t0 = time.perf_counter()
        results = self.model.predict(frame, conf=conf, verbose=False)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    "class_id": cls_id,
                    "class_name": CLASS_NAMES.get(cls_id, str(cls_id)),
                    "confidence": float(box.conf[0]),
                    "bbox": [float(v) for v in box.xyxy[0].tolist()],
                })
        return detections, latency_ms

    def draw(self, frame: np.ndarray, detections):
        """Draw bounding boxes + labels on a frame (for evidence snapshots)."""
        colors = {0: (0, 0, 255), 1: (0, 165, 255)}  # red=smoking, orange=phone
        for d in detections:
            x1, y1, x2, y2 = map(int, d["bbox"])
            color = colors.get(d["class_id"], (0, 255, 0))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{d['class_name']} {d['confidence']:.2f}"
            cv2.putText(frame, label, (x1, max(y1 - 8, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame


_detector_singleton = None


def get_detector() -> YOLODetector:
    global _detector_singleton
    if _detector_singleton is None:
        _detector_singleton = YOLODetector()
    return _detector_singleton
