import os, sys
sys.path.append(r'd:\\BME\\Semester_06\\Biomedical Signal Processing\\stitch_advanced_ecg_hrv_analysis_suite')
import streamlit as st
import numpy as np

# Minimal session state for chart generation
st.session_state['raw_signals'] = {'testfile': np.zeros(2500)}
st.session_state['cleaned_signals'] = {'testfile': np.zeros(2500)}
st.session_state['rpeaks'] = {'testfile': np.arange(0, 2500, 250)}
st.session_state['clean_rr_intervals'] = {'testfile': np.random.normal(800, 50, 100)}
st.session_state['raw_rr_intervals'] = {'testfile': np.random.normal(800, 60, 100)}
st.session_state['psd_data'] = {'testfile': (np.linspace(0,0.5,100), np.random.rand(100))}

# Dummy metrics
metrics = {'testfile': {
    'Mean HR (bpm)': 70,
    'SDNN (ms)': 50,
    'RMSSD (ms)': 30,
    'Confidence (%)': 95,
    'Mean RR (ms)': 800,
    'Mean RR (ms)': 800,
    'Mean RR (ms)': 800,
}}
settings = {'sfreq': 250, 'lowcut': 0.5, 'highcut': 40, 'filter_order':4, 'rpeak_method':'NeuroKit'}
sqi_cache = {}

from pages import 08_Report_Generation as rpt
# Build PDF
pdf_bytes = rpt.build_pdf_report(metrics, settings, sqi_cache)
print('PDF generated, size', len(pdf_bytes))
