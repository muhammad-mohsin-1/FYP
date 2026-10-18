"""Download + verify the CigDet cigarette dataset (Mendeley Data).

Source (verified 2026-10-18):
  Landing page : https://data.mendeley.com/datasets/6hyrr8typ7/1
  DOI          : 10.17632/6hyrr8typ7.1
  File         : CigDet_dataset.zip (34,686,? bytes)
  SHA-256      : ef2ab181b62e93198654a333ae82b80bf3e08eafcc53e3c865340665936bae41
  Contents     : 557 images with YOLO-format annotations (train 446 / test 111)

No login required. If the network drops mid-download the script resumes.
"""
import hashlib
import os
import time
import zipfile

import requests

URL = ("https://data.mendeley.com/public-files/datasets/6hyrr8typ7/"
       "files/24e3327e-155e-4565-ab44-8b45dc6445ee/file_downloaded")
SHA256 = "ef2ab181b62e93198654a333ae82b80bf3e08eafcc53e3c865340665936bae41"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")


def download(dest: str = None) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = dest or os.path.join(OUT_DIR, "CigDet_dataset.zip")
    for attempt in range(6):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            r = requests.get(URL, headers=headers, timeout=120, stream=True)
            mode = "ab" if (have and r.status_code == 206) else "wb"
            with open(dest, mode) as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
            break
        except Exception as e:  # noqa: BLE001 - flaky network, just retry
            print(f"attempt {attempt + 1} interrupted ({type(e).__name__}); retrying...")
            time.sleep(5)
    digest = hashlib.sha256(open(dest, "rb").read()).hexdigest()
    assert digest == SHA256, f"SHA-256 mismatch! got {digest}"
    print(f"verified {dest} ({os.path.getsize(dest)} bytes)")
    return dest


def extract(zip_path: str) -> str:
    target = os.path.join(OUT_DIR, "cigdet")
    if not os.path.exists(target):
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(target)
        print(f"extracted to {target}")
    return target


if __name__ == "__main__":
    zp = download()
    extract(zp)
