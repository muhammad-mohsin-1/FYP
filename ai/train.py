"""Train the custom YOLOv11 multi-class model (smoking + mobile_phone).

CPU-friendly defaults for pipeline validation on a low-resource machine.
For the production-quality model, follow ai/full_training_recipe_COLAB.md
(GPU, more epochs, larger imgsz).

Usage:
    python ai/train.py [--epochs 5] [--imgsz 416] [--batch 4]
"""
import argparse
import os

import torch

# Be a good citizen on shared machines: cap thread usage.
# 2 threads is the polite max on this 2-core VM (a video worker is active).
torch.set_num_threads(max(1, min(2, os.cpu_count() or 2)))

from ultralytics import YOLO  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--data", default="ai/dataset/yolo/data.yaml")
    ap.add_argument("--name", default="yolo11n_contraband_cpu")
    args = ap.parse_args()

    print(f"threads: {torch.get_num_threads()} | device: cpu")
    model = YOLO("yolo11n.pt")  # downloads ~5 MB COCO-pretrained nano weights on first run
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=1,          # low RAM footprint
        device="cpu",
        pretrained=True,    # transfer learning from COCO weights
        optimizer="AdamW",
        lr0=0.001,
        patience=20,
        save=True,
        plots=True,
        name=args.name,
        exist_ok=True,
    )
    print("training done. metrics:", results.results_dict)
    # Export the best weights next to the training script for the backend.
    best = os.path.join("runs", "detect", args.name, "weights", "best.pt")
    if os.path.exists(best):
        os.makedirs("ai/runs", exist_ok=True)
        import shutil
        shutil.copy(best, "ai/runs/best.pt")
        print("copied best.pt -> ai/runs/best.pt")


if __name__ == "__main__":
    main()
