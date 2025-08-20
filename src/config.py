# ---- L3 extractor settings ----
DATASET_DIR = r"D:\DS_Mini_2\manifest-1603198545583\NSCLC-Radiomics"

# Output folders (relative to repo root)
OUTPUT_L3_DIR = r"outputs\l3_slices"
LOGS_DIR = r"outputs\logs"
FIGURES_DIR = r"outputs\figures"

# Visualization window for muscle-friendly contrast (WL/WW)
WINDOW_LEVEL = 40     
WINDOW_WIDTH = 400    

# Lumbar band as a fraction of craniocaudal extent
LUMBAR_LOW_FRAC = 0.60   # 60% from head
LUMBAR_HIGH_FRAC = 0.75  # 75% from head

# Guardrails on number of slices to keep
MIN_LUMBAR_SLICES = 8
MAX_LUMBAR_SLICES = 20
