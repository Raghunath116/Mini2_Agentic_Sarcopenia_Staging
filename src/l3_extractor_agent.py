import os, sys, argparse, random, datetime
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from config import (
    DATASET_DIR, OUTPUT_L3_DIR, LOGS_DIR, FIGURES_DIR,
    WINDOW_LEVEL, WINDOW_WIDTH,
    LUMBAR_LOW_FRAC, LUMBAR_HIGH_FRAC,
    MIN_LUMBAR_SLICES, MAX_LUMBAR_SLICES
)
from utils import (
    ensure_dir, is_dicom, safe_dcmread, modality_of, series_uid,
    instance_number, z_position, to_hu, window_hu, save_png, write_csv
)

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def find_patient_dirs(dataset_root: str) -> List[str]:
    # Patients are immediate children (e.g., LUNG1-001)
    return [os.path.join(dataset_root, d) for d in os.listdir(dataset_root)
            if os.path.isdir(os.path.join(dataset_root, d))]

def collect_dicoms(root: str) -> List[str]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if is_dicom(fp):
                files.append(fp)
    return files

def group_ct_by_series(dicom_files: List[str]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for fp in dicom_files:
        ds = safe_dcmread(fp)
        if ds is None:
            continue
        if modality_of(ds) != "CT":
            continue
        uid = series_uid(ds)
        groups.setdefault(uid, []).append(fp)
    # filter tiny/garbage series
    return {k: v for k, v in groups.items() if len(v) >= 10}

def load_series_sorted(series_files: List[str]):
    dsets = []
    for fp in series_files:
        ds = safe_dcmread(fp)
        if ds is not None:
            dsets.append(ds)
    # sort by Z (then InstanceNumber)
    zs = [z_position(d) for d in dsets]
    if any(np.isfinite(zs)):
        dsets.sort(key=lambda d: (z_position(d), instance_number(d)))
    else:
        dsets.sort(key=lambda d: instance_number(d))
    return dsets

def choose_primary_series(groups: Dict[str, List[str]]) -> List[str]:
    if not groups:
        return []
    # choose CT series with most slices
    best_uid = max(groups.keys(), key=lambda k: len(groups[k]))
    return groups[best_uid]

def select_lumbar_indices(sorted_series) -> List[int]:
    n = len(sorted_series)
    if n == 0:
        return []
    zs = [z_position(ds) for ds in sorted_series]
    # use normalized Z if scan covers sufficient craniocaudal extent
    if np.all(np.isfinite(zs)) and (max(zs) - min(zs) > 50):
        z_min, z_max = float(min(zs)), float(max(zs))
        z_norm = [(z - z_min) / max((z_max - z_min), 1e-6) for z in zs]
        idx = [i for i, zn in enumerate(z_norm) if LUMBAR_LOW_FRAC <= zn <= LUMBAR_HIGH_FRAC]
    else:
        lo = int(LUMBAR_LOW_FRAC * n)
        hi = int(LUMBAR_HIGH_FRAC * n)
        idx = list(range(lo, hi + 1))

    # guardrails
    if len(idx) < MIN_LUMBAR_SLICES:
        center = (idx[len(idx)//2] if idx else int(0.68 * n))
        half = max(MIN_LUMBAR_SLICES // 2, 4)
        start = max(center - half, 0)
        end = min(center + half, n - 1)
        idx = list(range(start, end + 1))

    if len(idx) > MAX_LUMBAR_SLICES:
        step = max(1, int(np.floor(len(idx) / MAX_LUMBAR_SLICES)))
        idx = idx[::step][:MAX_LUMBAR_SLICES]

    return sorted(set(idx))

def save_lumbar_pngs(patient_id: str, sorted_series, indices: List[int], out_root: str) -> List[str]:
    out_dir = os.path.join(out_root, patient_id)
    ensure_dir(out_dir)
    saved = []
    for i in indices:
        ds = sorted_series[i]
        try:
            pixels = ds.pixel_array  # may need pylibjpeg/gdcm for compressed
        except Exception as e:
            # skip problematic slice
            continue
        hu = to_hu(ds, pixels)
        img8 = window_hu(hu, WINDOW_LEVEL, WINDOW_WIDTH)
        out_fp = os.path.join(out_dir, f"{i:04d}.png")
        save_png(img8, out_fp)
        saved.append(out_fp)
    return saved

def preview_montage(patient_id: str, png_paths: List[str], out_dir: str, k: int = 6):
    if not png_paths:
        return
    sample = png_paths if len(png_paths) <= k else random.sample(png_paths, k)
    cols = 3
    rows = int(np.ceil(len(sample) / cols))
    fig = plt.figure(figsize=(cols * 3, rows * 3))
    for idx, p in enumerate(sample, 1):
        ax = fig.add_subplot(rows, cols, idx)
        ax.imshow(plt.imread(p), cmap="gray")
        ax.axis("off")
        ax.set_title(os.path.basename(p), fontsize=8)
    ensure_dir(out_dir)
    out_fp = os.path.join(out_dir, f"{patient_id}_lumbar_preview.png")
    plt.tight_layout()
    plt.savefig(out_fp, dpi=150)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Production L3 Extractor Agent (percentile lumbar band)")
    parser.add_argument("--input", type=str, default=DATASET_DIR, help="Dataset root (patients under here)")
    parser.add_argument("--output", type=str, default=OUTPUT_L3_DIR, help="Where to write extracted slices")
    parser.add_argument("--figures", type=str, default=FIGURES_DIR, help="Where to save preview montages")
    parser.add_argument("--logcsv", type=str, default=os.path.join(LOGS_DIR, "l3_index.csv"), help="CSV index")
    parser.add_argument("--logtxt", type=str, default=os.path.join(LOGS_DIR, f"l3_run_{timestamp()}.txt"), help="run log")
    parser.add_argument("--preview", action="store_true", help="Save small montages")
    args = parser.parse_args()

    # ensure outputs
    ensure_dir(args.output); ensure_dir(os.path.dirname(args.logcsv)); ensure_dir(args.figures); ensure_dir(os.path.dirname(args.logtxt))

    # open run log
    with open(args.logtxt, "w", encoding="utf-8") as flog:
        def log(msg):
            print(msg)
            flog.write(msg + "\n"); flog.flush()

        log(f"[INFO] L3 Extractor start: {timestamp()}")
        log(f"[INFO] Input dataset: {args.input}")
        log(f"[INFO] Output dir: {args.output}")
        log(f"[INFO] Lumbar band: {LUMBAR_LOW_FRAC:.2f}-{LUMBAR_HIGH_FRAC:.2f}")
        log(f"[INFO] WL/WW: {WINDOW_LEVEL}/{WINDOW_WIDTH}")

        patients = find_patient_dirs(args.input)
        rows: List[Dict] = []
        ok, fail = 0, 0

        for pdir in tqdm(patients, desc="Patients"):
            pid = os.path.basename(pdir)
            try:
                dcm_files = collect_dicoms(pdir)
                if not dcm_files:
                    fail += 1; log(f"[WARN] {pid}: no DICOM files"); continue

                groups = group_ct_by_series(dcm_files)
                series_files = choose_primary_series(groups)
                if not series_files:
                    fail += 1; log(f"[WARN] {pid}: no CT series >= 10 slices"); continue

                sorted_series = load_series_sorted(series_files)
                if not sorted_series:
                    fail += 1; log(f"[WARN] {pid}: could not load CT series"); continue

                idx = select_lumbar_indices(sorted_series)
                if not idx:
                    fail += 1; log(f"[WARN] {pid}: no lumbar indices selected"); continue

                saved = save_lumbar_pngs(pid, sorted_series, idx, args.output)
                if len(saved) == 0:
                    fail += 1; log(f"[WARN] {pid}: no slices saved (decode?)"); continue

                if args.preview:
                    preview_montage(pid, saved, args.figures, k=6)

                for i, fp in zip(idx, saved):
                    rows.append({"PatientID": pid, "SliceIndex": i, "SavedPath": fp.replace("\\", "/")})
                ok += 1

            except Exception as e:
                fail += 1
                log(f"[ERROR] {pid}: {e}")

        # write index csv
        write_csv(args.logcsv, rows, fieldnames=["PatientID", "SliceIndex", "SavedPath"])
        log(f"[INFO] Patients processed ok={ok}, failed={fail}")
        log(f"[INFO] Index: {args.logcsv}")
        if args.preview:
            log(f"[INFO] Previews: {args.figures}")
        log(f"[INFO] Done: {timestamp()}")

if __name__ == "__main__":
    main()
