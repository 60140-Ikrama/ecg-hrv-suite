# Complete ECG & HRV Analysis Multi-Dashboard System

This document outlines the architecture, components, and strategy to build an interactive, multi-dashboard ECG and HRV analysis system targeted for an "Excellent" grade.

## User Review Required
> [!IMPORTANT]
> - Is the specific multipage structure (using Streamlit's `pages/` directory) acceptable for your multi-dashboard requirements?
> - The application will use Streamlit's session state to share settings and data between pages. Let me know if you would prefer Dash instead, but Streamlit is highly efficient for this type of linear/pipeline flow.
> - We will rely on Python libraries `neurokit2`, `scipy`, `numpy`, and `plotly`. Please confirm if you have these dependencies installed or if I should include a `requirements.txt`.

## Proposed Changes

We will create a modular Streamlit app organized with a main file and individual pages, alongside utility modules for signal processing, to keep the UI clean and code reusable. We will structure the directories on your `d:\` drive as requested, but the plan applies to the codebase architecture broadly.

---
### 1. Main Directory Application (`d:\BME\Semester_06\Biomedical Signal Processing\ecg_hrv_dashboard`)

We will create a root `app.py` functioning as the landing dashboard and flow-diagram visualizing the algorithmic pipeline.

#### [NEW] `app.py`
- Description: Serves as the landing page, introducing the system, displaying the Pipeline flow diagram (ECG → Preprocessing → R-Peaks → RR → Ectopic Removal → HRV Analysis → Dashboards) and system instructions. 

#### [NEW] `utils/signal_processing.py`
- Description: Core module containing functions for bandpass filtering, baseline wander removal, and noise filtering using `scipy.signal` and `neurokit2`.

#### [NEW] `utils/rpeak_detection.py`
- Description: Functions encapsulating NeuroKit2 or Pan-Tompkins methods for robust R-peak detection.

#### [NEW] `utils/hrv_analysis.py`
- Description: Modules to compute RR intervals, detect and correct ectopic beats (Linear / Spline interpolation), compute time-domain, frequency-domain (Welch’s PSD), and non-linear HRV metrics.

#### [NEW] `components/sidebar_settings.py`
- Description: Encapsulated sidebar component (Dashboard 9: Settings) that contains all controls (sampling freq, filter cutoffs, threshold, ectopic settings, HRV parameters, etc.) and propagates real-time changes to `st.session_state`. This is rendered on all relevant dashboards.

---
### 2. Dashboard Pages (`pages/`)

#### [NEW] `pages/01_Input_and_Acquisition.py`
- Description: Dashboard 1. Handles uploading of `.csv`, `.mat`, `.txt`, `.edf` files. Features batch multiple-file upload, saving inputs to `st.session_state`. 

#### [NEW] `pages/02_Preprocessing.py`
- Description: Dashboard 2. Applies the configured bandpass filter and baseline adjustments visually using Plotly.

#### [NEW] `pages/03_R_Peak_Detection.py`
- Description: Dashboard 3. Overlays R-peaks over the filtered ECG signal. Adjust thresholding interactively.

#### [NEW] `pages/04_RR_Intervals_and_Ectopics.py`
- Description: Dashboards 4 & 5. Displays RR tachogram, detects ectopic outliers, and visually interpolates clean RR intervals dynamically relying on sidebar settings.

#### [NEW] `pages/05_HRV_Analysis_Time_Freq.py`
- Description: Dashboards 6 & 7. Shows Time-domain KPI cards (SDNN, RMSSD) and Frequency-domain plots highlighting HF/LF bands and interprets Sympathetic Vs Parasympathetic tone.

#### [NEW] `pages/06_Non_Linear_HRV.py`
- Description: Dashboard 8. Plots Poincaré plot, computing SD1, SD2, and approximate entropy metrics.

#### [NEW] `pages/07_Multi_File_Comparison.py`
- Description: Dashboard 10. Loads batched files side-by-side. Provides summary tables crossing data computed for each file and overlays PSD.

#### [NEW] `pages/08_Report_Generation.py`
- Description: Report section capturing metrics generated and allowing download (likely CSV or text-based Markdown summary) to fulfill CLO3.

## Open Questions
> [!WARNING]
> Regarding files like `.mat` and `.edf`, importing usually requires `mne` or `scipy.io`. Should I assume standard layouts for these `.mat` files or is there a specific array shape/key that expects the ECG trace? Also, can I use `mne` for EDF files?

## Verification Plan
### Automated & Manual Verification
- We will construct the directory tree.
- I will verify functionality iteratively using `streamlit run app.py` and capturing Streamlit state.
- Validate that the ectopic beats are successfully removed and interpolated.
- Create tests on provided sample files like `s5_sit.csv` or `ecgpvc.dat` (which contains PVC beats for ectopic verification).
