"""Merge CigDet (smoking) + COCO cell-phone subset into one 2-class YOLO dataset.

Classes:
    0 -> smoking       (CigDet, Mendeley DOI 10.17632/6hyrr8typ7.1)
    1 -> mobile_phone  (COCO 2017, category_id 67 "cell phone")

Output layout (Ultralytics YOLO format):
    ai/dataset/yolo/
        images/train/*.jpg   labels/train/*.txt
        images/val/*.jpg     labels/val/*.txt
        data.yaml

Split: CigDet train -> train, CigDet test -> val,
       COCO phones  -> 80/20 stratified-by-source train/val.
"""
import json
import os
import random
import shutil
import zipfile

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw")
OUT = os.path.join(BASE, "yolo")
random.seed(42)


def ensure_dirs():
    for d in ("images/train", "images/val", "labels/train", "labels/val"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)


def copy_cigdet():
    """CigDet labels are already YOLO (class 0). Copy train->train, test->val."""
    with zipfile.ZipFile(os.path.join(RAW, "CigDet_dataset.zip")) as z:
        z.extractall(os.path.join(RAW, "cigdet"))
    counts = {"train": 0, "val": 0}
    for split, dest in (("train", "train"), ("test", "val")):
        src = os.path.join(RAW, "cigdet", "CigDet_dataset", split)
        for fname in sorted(os.listdir(src)):
            if not fname.endswith(".jpg"):
                continue
            stem = os.path.splitext(fname)[0]
            label = os.path.join(src, stem + ".txt")
            if not os.path.exists(label):
                continue
            new_stem = f"cigdet_{stem}"
            shutil.copy(os.path.join(src, fname), os.path.join(OUT, "images", dest, new_stem + ".jpg"))
            shutil.copy(label, os.path.join(OUT, "labels", dest, new_stem + ".txt"))
            counts[dest] += 1
    return counts


def copy_coco_phones():
    """Convert COCO [x,y,w,h] absolute boxes to YOLO normalized, class 1."""
    meta = json.load(open(os.path.join(RAW, "coco", "phone_images.json")))
    random.shuffle(meta)
    n_val = max(1, int(len(meta) * 0.2))
    counts = {"train": 0, "val": 0}
    for i, m in enumerate(meta):
        dest = "val" if i < n_val else "train"
        src_img = os.path.join(RAW, "coco", "images", m["file"])
        if not os.path.exists(src_img):
            continue
        with Image.open(src_img) as im:
            w, h = im.size
        lines = []
        for (x, y, bw, bh) in m["bboxes"]:
            xc, yc = (x + bw / 2) / w, (y + bh / 2) / h
            wn, hn = bw / w, bh / h
            if wn <= 0 or hn <= 0 or wn > 1 or hn > 1:
                continue
            lines.append(f"1 {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")
        if not lines:
            continue
        new_stem = f"coco_{m['id']:012d}"
        shutil.copy(src_img, os.path.join(OUT, "images", dest, new_stem + ".jpg"))
        open(os.path.join(OUT, "labels", dest, new_stem + ".txt"), "w").write("\n".join(lines) + "\n")
        counts[dest] += 1
    return counts


def write_yaml():
    yaml_text = (
        f"path: {OUT}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: smoking\n"
        "  1: mobile_phone\n"
    )
    open(os.path.join(OUT, "data.yaml"), "w").write(yaml_text)
    print("wrote data.yaml")


def main():
    ensure_dirs()
    c1 = copy_cigdet()
    print("cigdet:", c1)
    c2 = copy_coco_phones()
    print("coco phones:", c2)
    write_yaml()
    for split in ("train", "val"):
        ni = len(os.listdir(os.path.join(OUT, "images", split)))
        nl = len(os.listdir(os.path.join(OUT, "labels", split)))
        print(f"{split}: {ni} images, {nl} label files")


if __name__ == "__main__":
    main()
