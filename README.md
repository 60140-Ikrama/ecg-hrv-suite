# 🩺 Clinical Sentinel — Advanced ECG & HRV Analysis Suite

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)

A high-performance, research-grade biomedical signal processing platform built for deep clinical insight and comparative analytics. 

Designed for rigorous academic evaluation (OEL Assignments), this suite seamlessly integrates a **ground-up implementation of the Pan-Tompkins algorithm (CLO1)**, robust ectopic beat handling, and advanced physiological interpretation metrics **(CLO2/CLO3)** into a stunning, modular 8-dashboard architecture.

---

## 🎥 Application Demos

Here is a quick look at the Clinical Sentinel in action:

**1. Full Pipeline ECG & HRV Demo**
https://github.com/60140-Ikrama/ecg-hrv-suite/raw/master/Demo/Recording_Demo_ecg_hrv.mp4

**2. Application Settings & Configuration**
https://github.com/60140-Ikrama/ecg-hrv-suite/raw/master/Demo/Recording%20ECGHRV_Setting_app.mp4

*(Note: If videos do not play in the browser, you can download them directly from the `Demo/` folder in this repository).*

---

## ✨ Key Features & Capabilities

### 🎛️ 1. Multi-Stage Filtering & Signal Quality (SQI)
- **Signal Quality Index (SQI):** Auto-evaluates Spectral Energy, Kurtosis, and Baseline drift to generate an automated 0–100 quality score (Excellent/Good/Acceptable/Poor) and SNR in dB.
- **Adaptive Sub-QRS Filtering:** 40ms sliding window smoothing.
- **Harmonic Powerline Notch:** 50Hz/60Hz modes with automated harmonic suppression.
- **Dynamic Butterworth Bandpass:** Configurable filter order (2–5).

### ❤️ 2. R-Peak Detection (Custom CLO1 Implementation)
- **Pan-Tompkins (Custom):** From-scratch algorithmic implementation. Includes bandpass isolation, derivative, squaring, moving-window integration (150ms), and adaptive dual-thresholds.
- **Multi-Method Comparison:** Runs Custom Pan-Tompkins, NeuroKit, original Pan-Tompkins, and Hamilton simultaneously, scoring agreement percentage (±50ms) against the primary method.

### ⏱️ 3. Ectopic Correction & Anomaly Engine
- **Z-Score Anomaly Detection:** Classifies RR variations (e.g., Short RR/Tachycardia risk vs Long RR).
- **Interpolation & Correction:** Multi-method detection (median/mean/combined) paired with Linear or Cubic Spline interpolation to eliminate PVCs and artifacts before HRV calculation.

### 📈 4. Comprehensive HRV Analytics
- **Time-Domain:** Mean RR, SDNN, RMSSD, SDSD, NN50, pNN50, CV, and sliding-window **Trend Analysis**.
- **Frequency-Domain:** VLF, LF, HF, LF/HF Ratio, and Total Power. Uses Welch's PSD method with configurable `nperseg` / `noverlap`.
- **Non-Linear (Fractal & Entropy):** 
  - **Poincaré Plot** (SD1, SD2, Area)
  - **Sample Entropy (SampEn) & Approximate Entropy (ApEn)**
  - **Detrended Fluctuation Analysis (DFA):** Computes short-term (α1) and long-term (α2) scaling exponents.

### 📁 5. Batch Processing & Multi-File Comparison
- Load and cache multiple ECG files (`.dat`, `.csv`, `.mat`, `.edf`, `.txt`).
- **Dashboard 7 (Multi-File Comparison):** Automatically compares HRV metrics across all loaded files using Side-by-Side Bar Grids, Normalised Radar (Spider) Charts, PSD Overlays, and interactive **time-domain ECG Signal Overlays**.

### 📑 6. Automated Clinical Report Generation
- **Dashboard 8 (Report Generation):** Instantly builds a comprehensive, professional clinical report incorporating signal methodology, multi-file metrics, and automated physiological interpretations (e.g., Sympathovagal Balance, Autonomic Vagal Tone).
- **Rich Exports:** Download full reports natively in **PDF** (via ReportLab) and **DOCX** formats, including all Plotly charts (DFA, Poincaré, PSD, etc.) embedded directly into the document.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/60140-Ikrama/ecg-hrv-suite.git
   cd ecg-hrv-suite
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application:**
   ```bash
   streamlit run app.py
   ```
   The suite will automatically open in your browser at `http://localhost:8501`.

---

## 🗂️ Project Architecture

```text
ecg-hrv-suite/
├── app.py                             # Main landing page & pipeline entry point
├── components/                        # UI/UX, Theme, and Sidebar settings
│   ├── sidebar_settings.py            # Global interactive state controller
│   └── theme.py                       # Clinical Sentinel CSS & Chart templates
├── pages/                             # The 8 Core Dashboards
│   ├── 01_Input_and_Acquisition.py
│   ├── 02_Preprocessing.py
│   ├── 03_R_Peak_Detection.py
│   ├── 04_RR_Intervals_and_Ectopics.py
│   ├── 05_HRV_Analysis_Time_Freq.py
│   ├── 06_Non_Linear_HRV.py
│   ├── 07_Multi_File_Comparison.py
│   └── 08_Report_Generation.py
├── utils/                             # Core Signal Processing Modules
│   ├── data_loader.py                 # EDF, MAT, CSV, DAT parsers
│   ├── signal_processing.py           # SQI, Notch, Bandpass, Wavelet
│   ├── rpeak_detection.py             # Custom Pan-Tompkins & Multi-method
│   └── hrv_analysis.py                # Entropy, DFA, Z-scores, PSD
└── requirements.txt
```

---

## 🎓 Academic Alignment (OEL)

- **CLO1 (Algorithm Implementation):** Satisfied via `utils/rpeak_detection.py` (Custom Pan-Tompkins built from scratch without high-level wrapper libraries).
- **CLO2 (Signal Analysis):** Satisfied via `utils/hrv_analysis.py` (Multi-domain HRV mapping, Spectral Density, DFA).
- **CLO3 (Interpretation & Reporting):** Satisfied via `pages/08_Report_Generation.py` and the automatic clinical context engine.

---

## ⚖️ License & Terms of Use

> **PROPRIETARY AND CONFIDENTIAL**
> 
> This repository and all accompanying code, documentation, and media are the proprietary property of **Muhammad Ikrama**.
> 
> **All rights reserved.** Modification, distribution, and use of this software are strictly prohibited without prior explicit written permission from the author. For academic inquiries or to request permission to use this codebase, please contact the author directly.

---

*Developed for the Biomedical Signal Processing Open-Ended Lab (OEL). Built with Streamlit, Plotly, SciPy, NumPy, and ReportLab.*
