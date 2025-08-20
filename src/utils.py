import os, math, csv
from typing import List, Dict
import numpy as np
import pydicom
from pydicom.errors import InvalidDicomError
from PIL import Image

def ensure_dir(p: str):
    if p and not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

def is_dicom(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    # quick check by extension or DICM magic
    if path.lower().endswith(".dcm"):
        return True
    try:
        with open(path, "rb") as f:
            head = f.read(132)
        return head[-4:] == b"DICM"
    except Exception:
        return False

def safe_dcmread(fp: str):
    try:
        return pydicom.dcmread(fp, force=True, stop_before_pixels=False)
    except (InvalidDicomError, Exception):
        return None

def modality_of(ds) -> str:
    return str(getattr(ds, "Modality", "")).upper()

def series_uid(ds) -> str:
    return getattr(ds, "SeriesInstanceUID", None) or "UNKNOWN"

def instance_number(ds) -> int:
    try:
        return int(getattr(ds, "InstanceNumber", 0))
    except Exception:
        return 0

def z_position(ds) -> float:
    # Prefer ImagePositionPatient[2], fallback SliceLocation, else NaN
    try:
        return float(ds.ImagePositionPatient[2])
    except Exception:
        try:
            return float(ds.get("SliceLocation", math.nan))
        except Exception:
            return math.nan

def to_hu(ds, arr: np.ndarray) -> np.ndarray:
    slope = float(getattr(ds, "RescaleSlope", 1.0))
    intercept = float(getattr(ds, "RescaleIntercept", 0.0))
    return arr.astype(np.float32) * slope + intercept

def window_hu(hu: np.ndarray, wl: float, ww: float) -> np.ndarray:
    lo = wl - ww / 2.0
    hi = wl + ww / 2.0
    clipped = np.clip(hu, lo, hi)
    norm = (clipped - lo) / max(hi - lo, 1e-6)
    return (norm * 255.0).astype(np.uint8)

def save_png(img8: np.ndarray, fp: str):
    Image.fromarray(img8).save(fp)

def write_csv(path: str, rows: List[Dict], fieldnames: List[str]):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
