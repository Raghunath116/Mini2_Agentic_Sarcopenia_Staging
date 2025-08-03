import os
import json
import argparse
from datetime import datetime
from tcia_utils import nbia

# ============ CONFIG ============
DATA_DIR = "data/raw"
LOG_DIR = "logs"
TXT_LOG = os.path.join(LOG_DIR, "dataset_report.txt")
JSON_LOG = os.path.join(LOG_DIR, "dataset_report.json")
# ================================

def create_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def load_manifest(manifest_path):
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file '{manifest_path}' not found.")
    return manifest_path

def download_dataset(manifest_path):
    print(f"\n[INFO] Starting dataset download from manifest: {manifest_path}")
    nbia.downloadSeries(manifest_path, DATA_DIR)
    print("[INFO] Download complete.")

def generate_report():
    patient_dirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    total_patients = len(patient_dirs)
    total_slices = 0

    for patient in patient_dirs:
        for root, _, files in os.walk(os.path.join(DATA_DIR, patient)):
            total_slices += len([f for f in files if f.endswith(".dcm")])

    report = {
        "dataset_name": "NSCLC-Radiomics",
        "total_patients": total_patients,
        "total_slices": total_slices,
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_path": os.path.abspath(DATA_DIR)
    }

    # Save TXT report
    with open(TXT_LOG, "w") as f:
        f.write("Dataset Report – NSCLC-Radiomics\n")
        f.write("--------------------------------\n")
        f.write(f"Total Patients: {total_patients}\n")
        f.write(f"Total CT Slices: {total_slices}\n")
        f.write(f"Generated On: {report['generated_on']}\n")
        f.write(f"Data Path: {report['data_path']}\n")

    # Save JSON report
    with open(JSON_LOG, "w") as jf:
        json.dump(report, jf, indent=4)

    return report

def print_summary(report):
    print("\n================== DATASET PREPARATION COMPLETE ==================")
    print(f" Patients: {report['total_patients']}")
    print(f" CT Slices: {report['total_slices']}")
    print(f" Logs saved at: {os.path.abspath(LOG_DIR)}")
    print("=================================================================")
    print("\nNext Step: Run the L3 Slice Extraction Agent to isolate abdominal slices.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic Dataset Setup for NSCLC-Radiomics")
    parser.add_argument("--manifest", required=True, help="Path to NBIA manifest file (.tcia)")
    args = parser.parse_args()

    create_dirs()
    manifest = load_manifest(args.manifest)
    download_dataset(manifest)
    report = generate_report()
    print_summary(report)
