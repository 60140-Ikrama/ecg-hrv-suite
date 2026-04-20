import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.signal_processing import preprocess_ecg

st.set_page_config(page_title="Preprocessing", page_icon="🧹", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("🧹 Dashboard 2: ECG Preprocessing")
    st.markdown("Apply filters to remove noise and baseline wander.")
    
    if "active_file" not in st.session_state or st.session_state["active_file"] not in st.session_state.get("raw_signals", {}):
        st.warning("Please upload and select an ECG file in Dashboard 1.")
        return
        
    active_file = st.session_state["active_file"]
    raw_signal = st.session_state["raw_signals"][active_file]
    sfreq = st.session_state.get("sfreq", 250.0)
    
    # Retrieve filter settings from sidebar
    lowcut = st.session_state.get("lowcut", 0.5)
    highcut = st.session_state.get("highcut", 40.0)
    remove_baseline = st.session_state.get("baseline_wander", True)
    noise_method = st.session_state.get("noise_method", "None")
    
    st.info(f"Applying Preprocessing to **{active_file}**: Bandpass ({lowcut}-{highcut} Hz) | Baseline Removal: {remove_baseline} | Noise Method: {noise_method}")
    
    # Process signal
    with st.spinner("Filtering signal..."):
        clean_sig = preprocess_ecg(
            raw_signal, sfreq, 
            lowcut=lowcut, highcut=highcut, 
            remove_baseline=remove_baseline, 
            noise_method=noise_method
        )
        # Store for downstream
        if "cleaned_signals" not in st.session_state:
            st.session_state["cleaned_signals"] = {}
        st.session_state["cleaned_signals"][active_file] = clean_sig

    # Visualization
    time = np.arange(len(raw_signal)) / sfreq
    max_points = 50000
    step = max(1, len(raw_signal) // max_points)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time[::step], y=raw_signal[::step], 
        mode='lines', name='Raw Signal', line=dict(color='rgba(255, 255, 255, 0.3)', width=1)
    ))
    fig.add_trace(go.Scatter(
        x=time[::step], y=clean_sig[::step], 
        mode='lines', name='Filtered Signal', line=dict(color='#00ffcc', width=1.5)
    ))
    
    theme = st.session_state.get("plot_theme", "plotly_dark")
    fig.update_layout(
        title="Raw vs. Filtered ECG",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        template=theme,
        hovermode="x unified",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
