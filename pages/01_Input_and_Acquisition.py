import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

# Add parent path to allow imports from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.data_loader import load_ecg_file

st.set_page_config(page_title="Input & Acquisition", page_icon="📡", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("📡 Dashboard 1: ECG Input & Signal Acquisition")
    st.markdown("Upload single or multiple ECG files to begin the pipeline.")
    
    uploaded_files = st.file_uploader(
        "Upload ECG File(s) (.csv, .txt, .mat, .edf)", 
        type=["csv", "txt", "mat", "edf"], 
        accept_multiple_files=True
    )
    
    if "raw_signals" not in st.session_state:
        st.session_state["raw_signals"] = {}
        
    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state["raw_signals"]:
                try:
                    sig = load_ecg_file(file)
                    if sig is not None:
                        st.session_state["raw_signals"][file.name] = sig
                except Exception as e:
                    st.error(f"Error loading {file.name}: {e}")
                    
    if st.session_state.get("raw_signals"):
        st.success(f"Successfully loaded {len(st.session_state['raw_signals'])} file(s).")
        
        # File selector panel
        selected_file = st.selectbox("Select file to view:", list(st.session_state["raw_signals"].keys()))
        
        # Save active signal in session to be picked up by next dashboards automatically
        st.session_state["active_file"] = selected_file
        
        signal = st.session_state["raw_signals"][selected_file]
        
        # Plotting
        st.subheader(f"Raw ECG Signal: {selected_file}")
        
        sfreq = st.session_state.get("sfreq", 250.0)
        time = np.arange(len(signal)) / sfreq
        
        # Downsample for faster plotting if huge
        max_points = 50000
        step = max(1, len(signal) // max_points)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time[::step], 
            y=signal[::step], 
            mode='lines', 
            name='Raw Signal',
            line=dict(color='#1f77b4', width=1.5)
        ))
        
        theme = st.session_state.get("plot_theme", "plotly_dark")
        fig.update_layout(
            title="Raw ECG Signal",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude",
            template=theme,
            hovermode="x unified",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Number of samples: {len(signal)} | Duration: ~{len(signal)/sfreq:.2f} seconds")
    else:
        st.warning("Please upload at least one ECG file to proceed.")

if __name__ == "__main__":
    main()
