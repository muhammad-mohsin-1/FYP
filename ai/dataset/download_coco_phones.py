"""Download the COCO 2017 'cell phone' subset (mobile_phone class).

Source (verified 2026-10-18):
  Annotations : http://images.cocodataset.org/annotations/annotations_trainval2017.zip (241 MB)
  Docs        : https://docs.ultralytics.com/datasets/detect/coco
  Homepage    : https://cocodataset.org

COCO 2017 category_id 67 == "cell phone" (see the 80-class list in the
Ultralytics COCO docs). We parse instances_val2017.json (+ a slice of
instances_train2017.json), collect every image containing a cell phone,
and download only those images using the per-image "coco_url" field
from the annotation JSON itself. No login required.
"""
import json
import os
import time
import zipfile

import requests

ANNOT_ZIP_URL = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
CELL_PHONE_CAT_ID = 67
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "coco")
MAX_IMAGES = 400  # keep the CPU-friendly subset small


def fetch_annotations() -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "annotations_trainval2017.zip")
    if not os.path.exists(dest):
        print("downloading COCO annotations (241 MB)...")
        with requests.get(ANNOT_ZIP_URL, timeout=600, stream=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
    with zipfile.ZipFile(dest) as z:
        z.extractall(OUT_DIR)
    return os.path.join(OUT_DIR, "annotations")


def collect_phone_images(annot_dir: str):
    """Return [(image_id, file_name, coco_url, [bboxes])] for cell-phone images."""
    wanted = []
    for split in ("val2017", "train2017"):
        path = os.path.join(annot_dir, f"instances_{split}.json")
        data = json.load(open(path))
        imgs = {i["id"]: i for i in data["images"]}
        phone_anns = [a for a in data["annotations"]
                      if a["category_id"] == CELL_PHONE_CAT_ID and not a.get("iscrowd", 0)]
        by_img = {}
        for a in phone_anns:
            by_img.setdefault(a["image_id"], []).append(a["bbox"])  # [x,y,w,h]
        for img_id, bboxes in by_img.items():
            info = imgs[img_id]
            wanted.append((img_id, info["file_name"], info["coco_url"], bboxes, split))
            if len(wanted) >= MAX_IMAGES:
                return wanted
    return wanted


def download_images(wanted, target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    saved = []
    for img_id, fname, url, bboxes, split in wanted:
        dest = os.path.join(target_dir, fname)
        if os.path.exists(dest):
            saved.append((fname, bboxes, img_id))
            continue
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                open(dest, "wb").write(r.content)
                saved.append((fname, bboxes, img_id))
                break
            except Exception as e:  # noqa: BLE001
                print(f"  retry {fname}: {type(e).__name__}")
                time.sleep(3)
    print(f"saved {len(saved)}/{len(wanted)} phone images")
    return saved


if __name__ == "__main__":
    annot_dir = fetch_annotations()
    wanted = collect_phone_images(annot_dir)
    print(f"found {len(wanted)} images containing cell phones")
    saved = download_images(wanted, os.path.join(OUT_DIR, "images"))
    json.dump([{"file": f, "bboxes": b, "id": i} for f, b, i in saved],
              open(os.path.join(OUT_DIR, "phone_images.json"), "w"))
