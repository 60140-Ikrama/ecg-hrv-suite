"""Dashboard 2 — ECG Preprocessing with step-by-step visualisation"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header, COLORS, get_plot_layout, set_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.signal_processing import (remove_baseline_wander, apply_bandpass_filter,
                                      apply_notch_filter, apply_wavelet_denoise,
                                      apply_adaptive_filter, preprocess_ecg, compute_sqi)

st.set_page_config(page_title="Preprocessing · Clinical Sentinel",
                   page_icon="🧹", layout="wide")


def _stat_row(label, raw_val, clean_val, fmt=".4f"):
    return (f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
            f'border-bottom:1px solid #1e2023;font-family:Inter;font-size:0.75rem;">'
            f'<span style="color:#849396;">{label}</span>'
            f'<span style="color:#bac9cc;">{raw_val:{fmt}}</span>'
            f'<span style="color:#c3f400;">{clean_val:{fmt}}</span></div>')


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboard 2 · Preprocessing", badge="Filter", active_file=active)
    pipeline_status_bar("Filter")

    if not active or active not in st.session_state.get("raw_signals", {}):
        st.warning("⚠️  Load an ECG file in **📡 Input & Acquisition** first.")
        return

    raw    = st.session_state["raw_signals"][active]
    sfreq  = st.session_state.get("sfreq",          250.0)
    lowcut = st.session_state.get("lowcut",          0.5)
    highcut= st.session_state.get("highcut",         40.0)
    order  = st.session_state.get("filter_order",    4)
    rem_bl = st.session_state.get("remove_baseline", True)
    noise  = st.session_state.get("noise_method",    "None")

    # ── Adaptive Pipeline Logic (SQI-Aware) ──────────────────────────────────
    # 1. First, compute SQI on the raw signal to determine adaptive strategy
    sqi_raw = compute_sqi(raw, sfreq)
    
    # 2. Apply adaptive preprocessing
    clean, strategy = adaptive_preprocess_ecg(raw, sfreq, sqi_raw, lowcut=lowcut, 
                                             highcut=highcut, filter_order=order)
    
    # Store results
    if "cleaned_signals" not in st.session_state:
        st.session_state["cleaned_signals"] = {}
    st.session_state["cleaned_signals"][active] = clean
    
    if "sqi_cache" not in st.session_state:
        st.session_state["sqi_cache"] = {}
    st.session_state["sqi_cache"][active] = compute_sqi(clean, sfreq)

    # ── Step-by-step pipeline (for visualization) ────────────────────────────
    # Note: visualization steps are kept for the subplot section below
    steps  = {"Raw": raw.copy().astype(float)}
    if rem_bl:
        steps["Baseline Removed"] = remove_baseline_wander(steps["Raw"], sfreq)
    prev = list(steps.values())[-1]
    steps["Bandpass Filtered"] = apply_bandpass_filter(prev, sfreq, lowcut, highcut, order=order)
    prev = steps["Bandpass Filtered"]
    
    # Show adaptive strategy in the step list
    steps[f"Adaptive: {strategy}"] = clean

    # ── Settings chips ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.25rem;">
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;border-left:3px solid #00daf3;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">SQI Strategy</span><br>
        <span style="font-family:'Manrope';font-weight:700;color:#00daf3;">
          {strategy}</span>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">Bandpass</span><br>
        <span style="font-family:'Manrope';font-weight:700;color:#c3f5ff;">
          {lowcut:.2f} – {highcut:.0f} Hz (order {order})</span>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">Quality Label</span><br>
        <span style="font-family:'Manrope';font-weight:700;
                     color:{'#c3f400' if sqi_raw['quality_label'] in ['Excellent','Good'] else '#ffba38'};">
          {sqi_raw['quality_label']} ({sqi_raw['overall_sqi']}%)</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Overlay plot ─────────────────────────────────────────────────────────
    section_header("Raw vs Filtered ECG")
    t    = np.arange(len(raw)) / sfreq
    step = max(1, len(raw) // 50_000)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t[::step], y=raw[::step], mode='lines', name='Raw',
        line=dict(color=COLORS["outline"], width=1.0), opacity=0.55,
        hovertemplate="t=%{x:.3f}s<br>Raw=%{y:.4f}<extra>Raw</extra>"))
    fig.add_trace(go.Scatter(
        x=t[::step], y=clean[::step], mode='lines', name='Filtered',
        line=dict(color=COLORS["secondary_fixed"], width=1.8),
        hovertemplate="t=%{x:.3f}s<br>Filtered=%{y:.4f}<extra>Filtered</extra>"))
    set_layout(fig, "Filtered ECG Signal", xaxis_title="Time (s)", yaxis_title="Amplitude")
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True})

    # ── Step-by-step subplots ─────────────────────────────────────────────────
    if len(steps) > 2:
        section_header("Step-by-Step Pipeline Stages")
        from plotly.subplots import make_subplots
        n_steps = len(steps)
        fig2 = make_subplots(rows=n_steps, cols=1, shared_xaxes=True,
                             vertical_spacing=0.04,
                             subplot_titles=list(steps.keys()))
        palette = [COLORS["outline"], COLORS["primary_dim"],
                   COLORS["secondary_fixed"], COLORS["tertiary_fixed_dim"],
                   "#ffb4ab"]
        for row, (name, arr) in enumerate(steps.items(), start=1):
            color = palette[(row - 1) % len(palette)]
            fig2.add_trace(go.Scatter(
                x=t[::step], y=arr[::step], mode='lines',
                name=name, line=dict(color=color, width=1.2)),
                row=row, col=1)
        set_layout(fig2, "Pipeline Stage Visualization", xaxis_title="Time (s)", yaxis_title="Amplitude")
        fig2.update_layout(height=160 * n_steps, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Stats comparison ─────────────────────────────────────────────────────
    section_header("Signal Statistics — Raw vs Filtered")
    sqi_raw   = compute_sqi(raw,   sfreq)
    sqi_clean = compute_sqi(clean, sfreq)

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
        f'border-bottom:1px solid #1e2023;font-family:Inter;font-size:0.7rem;">'
        f'<span style="color:#849396;font-weight:700;">Metric</span>'
        f'<span style="color:#849396;">Raw</span>'
        f'<span style="color:#c3f400;">Filtered</span></div>'
        + _stat_row("Mean",          np.mean(raw),  np.mean(clean))
        + _stat_row("Std Dev",       np.std(raw),   np.std(clean))
        + _stat_row("Min",           raw.min(),     clean.min())
        + _stat_row("Max",           raw.max(),     clean.max())
        + _stat_row("Overall SQI",  sqi_raw["overall_sqi"],
                                    sqi_clean["overall_sqi"], fmt=".1f")
        + _stat_row("SNR (dB)",      sqi_raw["snr_db"],
                                    sqi_clean["snr_db"], fmt=".1f"),
        unsafe_allow_html=True)

    snr_gain = sqi_clean["snr_db"] - sqi_raw["snr_db"]
    if snr_gain > 0:
        st.success(f"✅ Filtering improved SNR by **{snr_gain:.1f} dB**")


if __name__ == "__main__":
    main()
