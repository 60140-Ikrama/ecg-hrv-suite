# 🫀 Advanced ECG & HRV Analysis System - Walkthrough

I have successfully designed and built the complete ECG and HRV Analysis Multi-Dashboard System in the `stitch_advanced_ecg_hrv_analysis_suite` directory.

## 🚀 How to Run the System

To launch your clinical-grade dashboard locally, open a terminal (or PowerShell) and run:

```bash
cd "D:/BME/Semester_06/Biomedical Signal Processing/stitch_advanced_ecg_hrv_analysis_suite"
pip install -r requirements.txt
streamlit run app.py
```

## 🛠️ Implementation Summary

The system is fully modular and follows the exact algorithmic HRV pipeline. Here is the breakdown:

### 📡 1. Dashboard 1: Signal Acquisition
- **Location:** `pages/01_Input_and_Acquisition.py`
- Handles `.csv`, `.mat`, `.txt`, and `.edf` batch uploads.
- Smooth interactive rendering of raw signals using Plotly.

### 🧹 2. Dashboard 2: Preprocessing
- **Location:** `pages/02_Preprocessing.py`
- Uses SciPy (`butter`, `filtfilt`) and PyWavelets for baseline wander removal and bandpass filtering. 
- Real-time comparison between raw and clean ECGs.

### ❤️ 3. Dashboard 3: R-Peak Detection
- **Location:** `pages/03_R_Peak_Detection.py`
- Exposes `NeuroKit2`, `Pan-Tompkins`, and `Hamilton` detection algorithms.

### ⏱️ & ⚠️ 4. Dashboards 4 & 5: RR Intervals & Ectopic Beats
- **Location:** `pages/04_RR_Intervals_and_Ectopics.py`
- Calculates the initial tachogram.
- **Critical Requirement Met:** Detects outliers continuously through moving medians and applies Spline/Linear interpolations gracefully, graphing affected vs unaffected regions distinctly.

### 📈 5. Dashboards 6, 7 & 8: HRV Analysis 
- **Location:** `pages/05_HRV_Analysis_Time_Freq.py` & `pages/06_Non_Linear_HRV.py`
- Completes accurate metrics (SDNN, RMSSD, pNN50).
- Fully features **Welch's PSD approach** marking HF and LF zones.
- Provides Poincaré non-linear metrics, computing the SD1/SD2 correlation ellipse automatically.

### ⚙️ 6. Dashboard 9: Global Settings Pipeline
- **Location:** `components/sidebar_settings.py`
- Integrated as a sidebar that updates Streamlit's `st.session_state` universally. Change a sampling frequency or ectopic threshold parameter on any dashboard and watch it apply downstream immediately.

### 📁 & 📑 7. Dashboards 10: Multi-File & Reports
- **Location:** `pages/07_Multi_File_Comparison.py` & `pages/08_Report_Generation.py`
- Statistically aggregates metrics securely allowing direct comparative bar-graphs.
- Provides the robust, auto-generated Markdown and CSV academic report (Targeting **CLO-3**, fully structured to achieve an 'Excellent' band evaluating Sympathetic vs Parasympathetic balance).

## 📌 Testing
- All core algorithmic steps (`signal_processing.py`, `rpeak_detection.py`, and `hrv_analysis.py`) exist cleanly scoped in the `utils/` package.
- It dynamically builds session states mapping data across the sequence.

> [!TIP]
> Ensure you run the file `app.py` first when spinning up Streamlit, as it anchors the multi-page engine gracefully.
