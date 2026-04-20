import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import detect_r_peaks

st.set_page_config(page_title="R-Peak Detection", page_icon="❤️", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("❤️ Dashboard 3: R-Peak Detection")
    st.markdown("Identify R-peaks systematically from the fully cleaned signal.")
    
    if "cleaned_signals" not in st.session_state or st.session_state.get("active_file") not in st.session_state.get("cleaned_signals", {}):
        st.warning("Please run Dashboard 2 (Preprocessing) first.")
        return
        
    active_file = st.session_state["active_file"]
    clean_sig = st.session_state["cleaned_signals"][active_file]
    sfreq = st.session_state.get("sfreq", 250.0)
    method = st.session_state.get("rpeak_method", "NeuroKit")
    
    st.info(f"Extracting R-peaks for **{active_file}** using algorithm: **{method}**")
    
    with st.spinner("Detecting R-peaks..."):
        try:
            rpeaks = detect_r_peaks(clean_sig, sfreq, method=method)
            
            if "rpeaks" not in st.session_state:
                st.session_state["rpeaks"] = {}
            st.session_state["rpeaks"][active_file] = rpeaks
            
            st.success(f"Detected {len(rpeaks)} R-peaks.")
        except Exception as e:
            st.error(f"Detection error: {e}")
            return

    # Visualization
    # To avoid crashing browser with massive scatter of all points, limit to first 10 seconds or allow zooming
    time = np.arange(len(clean_sig)) / sfreq
    
    # We will plot the whole signal but use step for the line, while keeping precise R-peaks
    max_points = 50000
    step = max(1, len(clean_sig) // max_points)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time[::step], y=clean_sig[::step], 
        mode='lines', name='Clean ECG', line=dict(color='#00ffcc', width=1.5)
    ))
    
    # Scatter for R-peaks
    rpeak_times = rpeaks / sfreq
    rpeak_amplitudes = clean_sig[rpeaks]
    
    fig.add_trace(go.Scatter(
        x=rpeak_times, y=rpeak_amplitudes, 
        mode='markers', name='R-Peaks', 
        marker=dict(color='#ff2b2b', size=6, symbol='cross')
    ))
    
    theme = st.session_state.get("plot_theme", "plotly_dark")
    fig.update_layout(
        title=f"R-Peak Detection ({method})",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        template=theme,
        hovermode="x unified",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
