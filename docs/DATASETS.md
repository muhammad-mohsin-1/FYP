# Datasets — Verified Sources

All links below were verified working on 2026-10-18. Never add a dataset link
here without verifying it first.

## 1. CigDet — Cigarette Detection Dataset (class: `smoking`)

| Field | Value |
|---|---|
| Landing page | https://data.mendeley.com/datasets/6hyrr8typ7/1 |
| DOI | 10.17632/6hyrr8typ7.1 |
| Contributor | Ali Khan |
| Published | 28 March 2024, Version 1 |
| License | check Mendeley page (academic use) |
| Images | 557 (train 446 / test 111) |
| Annotation format | YOLO `.txt` (normalized `class xc yc w h`), single class `0` |
| Annotation tool | LabelImg |
| Direct download (no login) | `https://data.mendeley.com/public-files/datasets/6hyrr8typ7/files/24e3327e-155e-4565-ab44-8b45dc6445ee/file_downloaded` |
| File | `CigDet_dataset.zip`, 34,689,636 bytes |
| SHA-256 | `ef2ab181b62e93198654a333ae82b80bf3e08eafcc53e3c865340665936bae41` |

Download + verify + extract:
```bash
python ai/dataset/download_cigdet.py
```
The script resumes broken downloads and asserts the SHA-256 before use.

**Citation (BibTeX):**
```bibtex
@misc{cigdet2024,
  title  = {CigDet (Cigarette Detection) Dataset},
  author = {Ali Khan},
  year   = {2024},
  doi    = {10.17632/6hyrr8typ7.1},
  url    = {https://data.mendeley.com/datasets/6hyrr8typ7/1}
}
```

## 2. COCO 2017 — `cell phone` subset (class: `mobile_phone`)

| Field | Value |
|---|---|
| Homepage | https://cocodataset.org |
| Annotations | http://images.cocodataset.org/annotations/annotations_trainval2017.zip (241 MB) |
| Images | `val2017` / `train2017` splits via per-image `coco_url` in the JSON |
| Class | `cell phone`, COCO category_id **67** (index 67 in the 80-class list) |
| Docs | https://docs.ultralytics.com/datasets/detect/coco |
| License | COCO images: Flickr, mostly CC-BY; annotations: CC-BY 4.0 |

We keep only images containing `category_id == 67` (non-crowd), cap at 400,
and convert `[x, y, w, h]` absolute boxes to YOLO normalized format as
class `1`:
```bash
python ai/dataset/download_coco_phones.py
```

**Citation:**
```bibtex
@inproceedings{lin2014microsoft,
  title     = {Microsoft COCO: Common Objects in Context},
  author    = {Lin, Tsung-Yi and Maire, Michael and Belongie, Serge and Hays, James
               and Perona, Pietro and Ramanan, Deva and Zitnick, C. Lawrence and Dollár, Piotr},
  booktitle = {ECCV},
  year      = {2014}
}
```

## 3. Roboflow "Smoking Dataset" — recommended for the FULL training run

| Field | Value |
|---|---|
| Platform | https://universe.roboflow.com (search "smoking") |
| Images | 2,337 labeled |
| Classes | `face`, `cigarette`, `smoker` |
| Cited in | Journal of Artificial Intelligence and Engineering Applications (YOLOv5 vs YOLOv8 smoking-behavior study) |
| Access | **needs a free Roboflow account + API key** (human step) |

Download after creating the key (do this on your own machine / Colab):
```python
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_FREE_KEY")          # roboflow.com -> Sign up -> Settings -> API key
project = rf.workspace().project("smoking")     # pick the exact smoking project slug
dataset = project.version(1).download("yolov11")
```
Merge its `cigarette` boxes into class `0` of our dataset to roughly
4-5x the smoking samples for the production model. See
`ai/full_training_recipe_COLAB.md`.

## Merged training dataset (this project)

`ai/dataset/prepare_yolo_dataset.py` builds:

```
ai/dataset/yolo/
  images/train/*.jpg   labels/train/*.txt
  images/val/*.jpg     labels/val/*.txt
  data.yaml            # names: {0: smoking, 1: mobile_phone}
```

- CigDet `train/` → our `train/` (class 0), CigDet `test/` → our `val/`
- COCO phones → 80/20 split into `train/` / `val/` (class 1)
- Label files are YOLO format: `<class> <x_center> <y_center> <width> <height>` (normalized)

## Rejected / not used

- **Open Images V5 boxable classes**: checked the official
  `class-descriptions-boxable.csv` (601 classes) — contains **no**
  cigarette/smoking/tobacco class. Not usable for this task.
- **HuggingFace `ccclllwww/smoker_img_detection`** (~2,900 images): image
  classification folders only (`smoking_*` / `not_smoking_*`), **no bounding
  boxes**. Not usable for detection training.
