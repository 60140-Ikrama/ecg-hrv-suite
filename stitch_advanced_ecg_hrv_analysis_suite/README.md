# 🫀 Clinical Sentinel — ECG & HRV Analysis Suite

A **professional, multi-dashboard ECG and Heart Rate Variability (HRV) analysis platform** built for academic (OEL) and clinical research purposes.

Built with Python · Streamlit · Plotly · NeuroKit2 · SciPy

---

## 🎯 System Goal

> **ECG Signal → Preprocessing → R-Peak Detection → RR Interval Extraction → Ectopic Beat Handling → HRV Analysis (Time + Frequency + Non-linear) → Multi-Dashboard Visualization**

---

## 🖥️ Dashboards

| # | Dashboard | Description |
|---|---|---|
| Home | Pipeline Overview | Full algorithmic pipeline visualizer |
| 1 | 📡 Signal Acquisition | Upload ECG files (.csv, .dat, .mat, .edf, .txt) — single or batch |
| 2 | 🧹 Preprocessing | Bandpass filter, baseline wander removal, wavelet/notch denoising |
| 3 | ❤️ R-Peak Detection | Pan-Tompkins, NeuroKit, Hamilton, Elgendi algorithms |
| 4+5 | ⏱️ RR & Ectopics | RR tachogram + ectopic detection & linear/spline interpolation |
| 6+7 | 📈 HRV Time + Freq | SDNN, RMSSD, pNN50 + Welch PSD with LF/HF band visualization |
| 8 | 🔬 Non-Linear HRV | Poincaré plot (SD1/SD2 ellipse), Sample Entropy |
| 9 | ⚙️ Settings | Full pipeline control via sidebar — updates all dashboards live |
| 10 | 📁 Multi-File Comparison | Side-by-side HRV metrics, PSD overlay, statistical table |
| CLO3 | 📑 Report Generation | Downloadable Markdown + CSV + Methods report |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd stitch_advanced_ecg_hrv_analysis_suite
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python -m streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

## 📦 Dependencies

```
streamlit>=1.30
pandas
numpy
scipy
plotly
neurokit2
PyWavelets
mne
```

---

## 🗂️ Project Structure

```
stitch_advanced_ecg_hrv_analysis_suite/
├── app.py                         # Main landing page
├── requirements.txt
├── .streamlit/
│   └── config.toml                # Stitch dark theme config
├── components/
│   ├── theme.py                   # Design system + CSS injection
│   └── sidebar_settings.py        # Global settings sidebar (Dashboard 9)
├── utils/
│   ├── data_loader.py             # Multi-format ECG file loader
│   ├── signal_processing.py       # Filters (bandpass, notch, wavelet)
│   ├── rpeak_detection.py         # R-peak algorithms via NeuroKit2
│   └── hrv_analysis.py            # HRV metrics, ectopic correction
└── pages/
    ├── 01_Input_and_Acquisition.py
    ├── 02_Preprocessing.py
    ├── 03_R_Peak_Detection.py
    ├── 04_RR_Intervals_and_Ectopics.py
    ├── 05_HRV_Analysis_Time_Freq.py
    ├── 06_Non_Linear_HRV.py
    ├── 07_Multi_File_Comparison.py
    └── 08_Report_Generation.py
```

---

## 🧠 Algorithmic Pipeline

```
ECG Acquisition (.csv / .dat / .mat / .edf)
        │
        ▼
  Preprocessing
  ├── Baseline wander removal (high-pass @ 0.5 Hz)
  ├── Bandpass filter (default 0.5–40 Hz)
  └── Optional: Wavelet / Powerline Notch filter
        │
        ▼
  R-Peak Detection
  └── Methods: NeuroKit | Pan-Tompkins | Hamilton | Elgendi
        │
        ▼
  RR Interval Extraction
  └── RR = Δt between consecutive R-peaks (ms)
        │
        ▼
  Ectopic Beat Correction  ← CRITICAL
  ├── Detection: Moving-median deviation rule
  └── Correction: Linear | Spline interpolation
        │
        ▼
  HRV Analysis
  ├── Time-Domain: SDNN, RMSSD, NN50, pNN50, Mean RR
  ├── Frequency-Domain: Welch PSD, LF/HF bands, ratio
  └── Non-Linear: Poincaré (SD1, SD2), Sample Entropy
        │
        ▼
  Multi-Dashboard Visualization + Report Export
```

---

## 📑 Report (CLO3)

The **Report Generation** page produces:
- **Markdown report** — Methodology, results table, clinical interpretations
- **CSV metrics export** — All HRV metrics for all analyzed files
- **Methods summary text** — Pipeline parameters for academic submission

---

## 🎨 Design

Styled using the **Clinical Sentinel Stitch Design System**:
- Dark mode with `#111316` background
- Primary cyan accent `#00daf3` / `#c3f5ff`
- Google Fonts: **Manrope** (headlines) + **Inter** (body)
- KPI cards, glass-panel overlays, ECG grid backgrounds

---

## 📄 License

For academic use — Biomedical Signal Processing OEL, Semester 6.
