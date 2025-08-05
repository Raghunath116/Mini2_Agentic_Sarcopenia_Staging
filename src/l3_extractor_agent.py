import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from config import DATASET_DIR, OUTPUT_L3_DIR, LOGS_DIR, FIGURES_DIR, L3_Z_MIN, L3_Z_MAX, EXTRACTION_BUFFER

# Ensure directories exist
os.makedirs(OUTPUT_L3_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def load_dicom_series(folder):
    slices = []
    for f in os.listdir(folder):
        if f.endswith(".dcm"):
            ds = pydicom.dcmread(os.path.join(folder, f))
            if hasattr(ds, "ImagePositionPatient"):
                slices.append(ds)
    slices.sort(key=lambda x: x.ImagePositionPatient[2])  # Sort by Z-axis
    return slices

def find_l3_slices(slices):
    z_positions = [s.ImagePositionPatient[2] for s in slices]
    z_array = np.array(z_positions)

    # Find indices in the L3 range
    l3_indices = np.where((z_array >= L3_Z_MIN) & (z_array <= L3_Z_MAX))[0]
    if len(l3_indices) == 0:
        return []

    # Take buffer around the center
    center = l3_indices[len(l3_indices)//2]
    start = max(center - EXTRACTION_BUFFER, 0)
    end = min(center + EXTRACTION_BUFFER, len(slices)-1)
    return list(range(start, end+1))

def save_slices(patient_id, slices, indices):
    out_dir = os.path.join(OUTPUT_L3_DIR, patient_id)
    os.makedirs(out_dir, exist_ok=True)
    saved_paths = []
    for idx in indices:
        pixel_array = slices[idx].pixel_array
        # Normalize to 0-255
        pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
        out_path = os.path.join(out_dir, f"{idx}.png")
        plt.imsave(out_path, pixel_array, cmap="gray")
        saved_paths.append(out_path)
    return saved_paths

def extract_l3_for_all():
    patients = os.listdir(DATASET_DIR)
    log_file = open(os.path.join(LOGS_DIR, "l3_extraction_log.csv"), "w")
    log_file.write("PatientID,ExtractedSlices\n")

    for patient in tqdm(patients, desc="Processing patients"):
        patient_path = os.path.join(DATASET_DIR, patient)
        if not os.path.isdir(patient_path): continue

        # Search for CT series folder (has most slices)
        series_folders = [os.path.join(patient_path, s) for s in os.listdir(patient_path)]
        ct_folder = max(series_folders, key=lambda sf: len(os.listdir(sf)))

        slices = load_dicom_series(ct_folder)
        if len(slices) == 0: continue

        l3_indices = find_l3_slices(slices)
        if len(l3_indices) == 0: continue

        saved_paths = save_slices(patient, slices, l3_indices)
        log_file.write(f"{patient},{len(saved_paths)}\n")

    log_file.close()
    print(f"[INFO] Extraction complete. Logs saved to {LOGS_DIR}")

def preview_random(patient_count=3):
    import random
    patients = os.listdir(OUTPUT_L3_DIR)
    sample_patients = random.sample(patients, min(patient_count, len(patients)))
    for patient in sample_patients:
        imgs = os.listdir(os.path.join(OUTPUT_L3_DIR, patient))
        sample_img = os.path.join(OUTPUT_L3_DIR, patient, random.choice(imgs))
        img = plt.imread(sample_img)
        plt.imshow(img, cmap="gray")
        plt.title(f"Preview: {patient}")
        plt.show()

if __name__ == "__main__":
    extract_l3_for_all()
    preview_random()
