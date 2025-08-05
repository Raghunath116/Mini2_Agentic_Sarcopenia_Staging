# === Global Config for Project Paths ===

# Raw dataset location (change if needed)
DATA_DIR = "D:/DS_Mini_2"       # where your NSCLC-Radiomics data lives
PROCESSED_DIR = "data/processed"  # where processed L3 slices will be saved
LOG_DIR = "logs"                  # where all logs go

# Project metadata
PROJECT_NAME = "Mini2_Agentic_Sarcopenia_Staging"
DATASET_NAME = "NSCLC-Radiomics"

# Paths for L3 extractor
DATASET_DIR = r"D:\DS_Mini_2\manifest-1603198545583\NSCLC-Radiomics"
OUTPUT_L3_DIR = r"outputs\l3_slices"
LOGS_DIR = r"outputs\logs"
FIGURES_DIR = r"outputs\figures"

# L3 slice detection thresholds
L3_Z_MIN = -250
L3_Z_MAX = -100
EXTRACTION_BUFFER = 5  # ± slices around L3 center
