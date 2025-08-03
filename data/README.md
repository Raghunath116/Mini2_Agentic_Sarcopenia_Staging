# Data Directory – NSCLC-Radiomics

This directory contains the **NSCLC-Radiomics** dataset for our project:  
**Agentic AI for Multi-Class Sarcopenia Staging**.

---

## **How to Get the Data**

### **Manual Download**
1. Go to the [NSCLC-Radiomics collection on TCIA](https://wiki.cancerimagingarchive.net/display/Public/NSCLC-Radiomics).
2. Use the **NBIA Data Retriever** tool to download the dataset.
3. Save it inside `data/raw/`.

---

### **Automated Download (Recommended)**
1. Place the NBIA `.tcia` manifest file in the root folder.
2. Run the agent:
   ```bash
   python src/agent_dataset_setup.py --manifest NSCLC-Radiomics.manifest
