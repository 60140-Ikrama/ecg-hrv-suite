# 🩺 Clinical Sentinel — Advanced ECG & HRV Analysis Suite

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A high-performance, research-grade biomedical signal processing platform built for deep clinical insight, automated cardiovascular risk detection, and comparative analytics.

Designed for rigorous academic evaluation (OEL Assignments), this suite integrates a **ground-up implementation of the Pan-Tompkins algorithm (CLO1)**, robust ectopic beat handling, **heart disease detection (rule-based + ML)**, and advanced physiological interpretation **(CLO2/CLO3)** into a modular **11-dashboard architecture**.

---

## 🔗 Live App & Repository

**🌐 Deployed App:** https://ecg-hrv-suite.streamlit.app

**📦 GitHub:** https://github.com/60140-Ikrama/ecg-hrv-suite

**QR Code:** Auto-generated and displayed live on the app home page footer — scan to open the repo on your phone.

---

## 🎥 Application Demos

**1. Full Pipeline ECG & HRV Demo**
https://github.com/60140-Ikrama/ecg-hrv-suite/raw/master/Demo/Recording_Demo_ecg_hrv.mp4

**2. Application Settings & Configuration**
https://github.com/60140-Ikrama/ecg-hrv-suite/raw/master/Demo/Recording%20ECGHRV_Setting_app.mp4

*(Download from `Demo/` folder if browser won't play inline.)*

---

## ✨ Key Features & Capabilities

### 🎛️ 1. Multi-Stage Filtering & Signal Quality (SQI)
- Spectral Energy, Kurtosis, Baseline drift → 0–100 quality score + SNR in dB.
- Adaptive Sub-QRS Filtering, Harmonic Powerline Notch (50/60 Hz), Butterworth Bandpass.

### ❤️ 2. R-Peak Detection (Custom CLO1 Implementation)
- **Pan-Tompkins (Custom):** Built from scratch — bandpass, derivative, squaring, 150ms MWI, adaptive dual-thresholds.
- **Multi-Method Comparison:** Custom, NeuroKit, original Pan-Tompkins, Hamilton — simultaneous scoring.

### ⏱️ 3. Ectopic Correction & Anomaly Engine
- Z-Score anomaly detection (Short RR/Tachycardia vs Long RR/Bradycardia).
- Multi-method detection (median/mean/combined) + Linear or Cubic Spline interpolation.

### 📈 4. Comprehensive HRV Analytics
- **Time-Domain:** Mean RR, SDNN, RMSSD, SDSD, NN50, pNN50, CV, sliding-window trend.
- **Frequency-Domain:** VLF, LF, HF, LF/HF, Total Power — Welch's PSD, configurable bands.
- **Non-Linear:** Poincaré (SD1, SD2), Sample Entropy, ApEn, DFA (α1, α2).

### 🫀 5. Heart Disease Detection *(NEW — v2.1)*
- **Rule-Based Classifier:** Clinical HRV thresholds for SDNN, RMSSD, LF/HF Ratio, DFA α1, Mean HR, Ectopic Rate.
- **ML-Enhanced Classifier:** Random Forest trained inline on synthetic HRV reference ranges — no external `.pkl` file required.
- **Risk Output:** `Normal` / `Mild Risk` / `High Risk` with weighted risk score (0–100), confidence %, per-metric flags, and clinical explanation paragraph.
- **Fully integrated into PDF reports** with risk assessment table.

### 📁 6. Multi-File Analysis & Comparison (1 to 5+ files)
- Side-by-side HRV bar grids, Radar (Spider) Charts, PSD Overlays, scatter concordance plots.
- Statistical Δ difference tables between any two files.
- Comparative risk score bar chart across all loaded files.

### 📑 7. Automated Clinical Report Generation
- **PDF** (ReportLab) + **DOCX** exports — full metrics, all charts, clinical interpretation, risk assessment.
- **8 Charts per file:** Raw ECG, Filtered ECG, R-Peak overlay, RR Tachogram, **RR Histogram** *(NEW)*, Ectopic Correction, PSD, Poincaré, DFA.
- **Multi-file comparison summary page** auto-appended to PDF when >1 file is loaded.

### 📐 8. QR Code *(NEW — v2.1)*
- Auto-generated QR code displayed on home page footer linking to GitHub repository.
- Requires `qrcode[pil]` (graceful fallback to text link if not installed).

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/60140-Ikrama/ecg-hrv-suite.git
   cd ecg-hrv-suite
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application:**
   ```bash
   streamlit run app.py
   ```
   Opens automatically at `http://localhost:8501`.

---

## 🗂️ Project Architecture

```text
ecg-hrv-suite/
├── app.py                               # Main landing page (11-dashboard hub, QR code)
├── components/
│   ├── sidebar_settings.py              # Global interactive state controller
│   └── theme.py                         # Clinical Sentinel CSS & chart templates
├── pages/
│   ├── 01_Input_and_Acquisition.py      # File upload & URL download
│   ├── 02_Preprocessing.py              # Filtering, SQI scoring
│   ├── 03_R_Peak_Detection.py           # Pan-Tompkins + multi-method comparison
│   ├── 04_RR_Intervals_and_Ectopics.py  # RR tachogram, histogram, ectopic correction
│   ├── 05_HRV_Analysis_Time_Freq.py     # Time & frequency domain HRV
│   ├── 06_Non_Linear_HRV.py             # Poincaré, DFA, entropy
│   ├── 07_Multi_File_Comparison.py      # Side-by-side multi-file analysis
│   ├── 08_Report_Generation.py          # PDF + DOCX export with risk section
│   └── 09_Heart_Disease_Detection.py    # ← NEW: Cardiovascular risk assessment
├── utils/
│   ├── data_loader.py                   # EDF, MAT, CSV, DAT parsers
│   ├── signal_processing.py             # SQI, Notch, Bandpass, Wavelet
│   ├── rpeak_detection.py               # Custom Pan-Tompkins & multi-method
│   ├── hrv_analysis.py                  # Entropy, DFA, Z-scores, PSD
│   ├── heart_disease_detection.py       # ← NEW: Rule-based + ML classifier
│   └── qr_generator.py                  # ← NEW: QR code PNG generator
├── Demo/                                # Demo videos
├── Reports/                             # Generated report outputs
├── requirements.txt
└── LICENSE
```

---

## 🎓 Academic Alignment (OEL)

| CLO | Implementation |
|-----|----------------|
| **CLO1** (Algorithm) | `utils/rpeak_detection.py` — Custom Pan-Tompkins from scratch |
| **CLO2** (Analysis) | `utils/hrv_analysis.py` — Multi-domain HRV (time/freq/nonlinear) |
| **CLO3** (Reporting) | `pages/08_Report_Generation.py` + `pages/09_Heart_Disease_Detection.py` — Clinical interpretation, automated risk scoring, PDF/DOCX export |

---

## ⚙️ Dependencies

```
streamlit>=1.30  pandas  numpy  scipy  plotly
neurokit2  PyWavelets  mne  reportlab  python-docx
kaleido  scikit-learn  qrcode[pil]  Pillow
```

---

## ⚖️ License

MIT License — see `LICENSE` file.

*Developed for the Biomedical Signal Processing Open-Ended Lab (OEL). Built with Streamlit, Plotly, SciPy, NumPy, ReportLab, and scikit-learn.*
