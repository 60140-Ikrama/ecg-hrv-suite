import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import get_rr_intervals
from utils.hrv_analysis import remove_ectopic_beats

st.set_page_config(page_title="RR Intervals & Ectopics", page_icon="⏱️", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("⏱️ Dashboards 4 & 5: RR Intervals and Ectopic Correction")
    st.markdown("Extract heart rate variability (HRV) time-series and remove outliers (ectopic beats).")
    
    if "rpeaks" not in st.session_state or st.session_state.get("active_file") not in st.session_state.get("rpeaks", {}):
        st.warning("Please run Dashboard 3 (R-Peak Detection) first.")
        return
        
    active_file = st.session_state["active_file"]
    rpeaks = st.session_state["rpeaks"][active_file]
    sfreq = st.session_state.get("sfreq", 250.0)
    
    # 1. Calculate RR intervals
    raw_rr = get_rr_intervals(rpeaks, sfreq)
    
    # 2. Get Settings
    enable_correction = st.session_state.get("remove_ectopic", True)
    threshold = st.session_state.get("ectopic_threshold", 0.20)
    method = st.session_state.get("ectopic_interp", "Linear")
    
    if enable_correction:
        clean_rr, outliers_mask = remove_ectopic_beats(raw_rr, method=method, threshold=threshold)
        msg = f"Ectopic checking active. Removed {np.sum(outliers_mask)} outliers."
    else:
        clean_rr = raw_rr
        outliers_mask = np.zeros(len(raw_rr), dtype=bool)
        msg = "Ectopic checking disabled."
        
    st.info(msg)
    
    # Store clean RR for HRV modules
    if "clean_rr_intervals" not in st.session_state:
        st.session_state["clean_rr_intervals"] = {}
    st.session_state["clean_rr_intervals"][active_file] = clean_rr
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    theme = st.session_state.get("plot_theme", "plotly_dark")
    
    with col1:
        st.subheader("Raw RR Series (Tachogram)")
        fig_raw = go.Figure()
        
        # Plot continuous lines
        fig_raw.add_trace(go.Scatter(y=raw_rr, mode='lines+markers', name='Raw RR', line=dict(color='#ffaa00')))
        
        # Highlight outliers
        if np.any(outliers_mask):
            fig_raw.add_trace(go.Scatter(
                x=np.where(outliers_mask)[0], 
                y=raw_rr[outliers_mask],
                mode='markers', name='Detected Ectopics',
                marker=dict(color='red', size=8, symbol='x')
            ))
            
        fig_raw.update_layout(xaxis_title="Beat Number", yaxis_title="RR Interval (ms)", template=theme, height=400)
        st.plotly_chart(fig_raw, use_container_width=True)
        
    with col2:
        st.subheader("Corrected RR Series")
        fig_clean = go.Figure()
        fig_clean.add_trace(go.Scatter(y=clean_rr, mode='lines+markers', name='Clean RR', line=dict(color='#00ccff')))
        
        # Highlight interpolations
        if np.any(outliers_mask):
            fig_clean.add_trace(go.Scatter(
                x=np.where(outliers_mask)[0], 
                y=clean_rr[outliers_mask],
                mode='markers', name='Interpolated Points',
                marker=dict(color='#00ff00', size=8)
            ))
            
        fig_clean.update_layout(xaxis_title="Beat Number", yaxis_title="RR Interval (ms)", template=theme, height=400)
        st.plotly_chart(fig_clean, use_container_width=True)

if __name__ == "__main__":
    main()
