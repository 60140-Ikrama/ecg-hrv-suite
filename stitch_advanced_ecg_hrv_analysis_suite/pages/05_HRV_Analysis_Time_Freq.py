import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import get_time_domain_hrv, get_freq_domain_hrv

st.set_page_config(page_title="HRV Analysis", page_icon="📈", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("📈 Dashboards 6 & 7: Time & Frequency HRV")
    
    if "clean_rr_intervals" not in st.session_state or st.session_state.get("active_file") not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("Please process RR intervals in Dashboard 4/5 first.")
        return
        
    active_file = st.session_state["active_file"]
    clean_rr = st.session_state["clean_rr_intervals"][active_file]
    
    st.markdown(f"### Analysis for **{active_file}**")
    
    tab1, tab2 = st.tabs(["Dashboard 6: Time-Domain HRV", "Dashboard 7: Frequency-Domain HRV"])
    
    theme = st.session_state.get("plot_theme", "plotly_dark")
    
    # --- TIME DOMAIN ---
    with tab1:
        st.subheader("Time-Domain Metrics")
        time_metrics = get_time_domain_hrv(clean_rr)
        
        # Save to state for multipage/reports
        if "metrics" not in st.session_state:
            st.session_state["metrics"] = {}
        if active_file not in st.session_state["metrics"]:
            st.session_state["metrics"][active_file] = {}
        st.session_state["metrics"][active_file].update(time_metrics)
        
        # KPI Cards
        cols = st.columns(5)
        cols[0].metric("Mean RR", f"{time_metrics.get('Mean RR (ms)', 0):.1f} ms")
        cols[1].metric("SDNN", f"{time_metrics.get('SDNN (ms)', 0):.1f} ms")
        cols[2].metric("RMSSD", f"{time_metrics.get('RMSSD (ms)', 0):.1f} ms")
        cols[3].metric("NN50", f"{time_metrics.get('NN50', 0)}")
        cols[4].metric("pNN50", f"{time_metrics.get('pNN50 (%)', 0):.1f} %")
        
        st.markdown("""
        **Clinical Context:**
        - **SDNN**: Reflects overall HRV (long-term variability). Correlates with total power.
        - **RMSSD**: Primary time-domain measure of short-term, parasympathetic (vagal) variation.
        """)

    # --- FREQUENCY DOMAIN ---
    with tab2:
        st.subheader("Frequency-Domain Metrics (Welch's PSD)")
        
        vlf_band = (0.003, 0.04)
        lf_band = (st.session_state.get("lf_min", 0.04), st.session_state.get("lf_max", 0.15))
        hf_band = (st.session_state.get("hf_min", 0.15), st.session_state.get("hf_max", 0.40))
        
        freq_metrics, freqs, psd = get_freq_domain_hrv(clean_rr, vlf_band=vlf_band, lf_band=lf_band, hf_band=hf_band)
        
        if freq_metrics:
            st.session_state["metrics"][active_file].update(freq_metrics)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LF Power", f"{freq_metrics['LF Power']:.2f}")
            c2.metric("HF Power", f"{freq_metrics['HF Power']:.2f}")
            c3.metric("LF/HF Ratio", f"{freq_metrics['LF/HF Ratio']:.2f}")
            c4.metric("Total Power", f"{freq_metrics['Total Power']:.2f}")
            
            # Plot PSD
            fig_psd = go.Figure()
            fig_psd.add_trace(go.Scatter(x=freqs, y=psd, mode='lines', name='PSD', line=dict(color='white')))
            
            # Highlight bands
            idx_vlf = np.logical_and(freqs >= vlf_band[0], freqs < vlf_band[1])
            idx_lf = np.logical_and(freqs >= lf_band[0], freqs < lf_band[1])
            idx_hf = np.logical_and(freqs >= hf_band[0], freqs < hf_band[1])
            
            fig_psd.add_trace(go.Scatter(x=freqs[idx_vlf], y=psd[idx_vlf], fill='tozeroy', name='VLF', mode='none', fillcolor='rgba(200,200,200,0.4)'))
            fig_psd.add_trace(go.Scatter(x=freqs[idx_lf], y=psd[idx_lf], fill='tozeroy', name='LF', mode='none', fillcolor='rgba(255,165,0,0.5)'))
            fig_psd.add_trace(go.Scatter(x=freqs[idx_hf], y=psd[idx_hf], fill='tozeroy', name='HF', mode='none', fillcolor='rgba(0,191,255,0.5)'))
            
            fig_psd.update_layout(
                title="Power Spectral Density",
                xaxis_title="Frequency (Hz)",
                yaxis_title="Density (ms²/Hz)",
                template=theme,
                xaxis=dict(range=[0, 0.5]) # Typical HRV range focus
            )
            st.plotly_chart(fig_psd, use_container_width=True)
            
            st.info("""
            **Physiological Interpretation:**
            * **HF (High Frequency)**: Modulated by Parasympathetic (Vagal) tone. Associated with respiratory sinus arrhythmia.
            * **LF (Low Frequency)**: Modulated by both Sympathetic and Parasympathetic activities.
            * **LF/HF Ratio**: Often used as an index of Sympathovagal balance.
            """)
        else:
            st.warning("Not enough RR data for reliable frequency analysis.")

if __name__ == "__main__":
    main()
