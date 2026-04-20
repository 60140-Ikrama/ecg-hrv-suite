"""Dashboard 2 — ECG Preprocessing"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.signal_processing import preprocess_ecg

st.set_page_config(page_title="Preprocessing · Clinical Sentinel", page_icon="🧹", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboard 2 · Preprocessing", badge="Filter", active_file=active)
    pipeline_status_bar("Filter")

    if not active or active not in st.session_state.get("raw_signals", {}):
        st.warning("⚠️  Load an ECG file in **📡 Input & Acquisition** first.")
        return

    raw = st.session_state["raw_signals"][active]
    sfreq = st.session_state.get("sfreq", 250.0)
    lowcut = st.session_state.get("lowcut", 0.5)
    highcut = st.session_state.get("highcut", 40.0)
    remove_bl = st.session_state.get("remove_baseline", True)
    noise = st.session_state.get("noise_method", "None")

    # ── Info bar ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.25rem;">
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">Bandpass</span><br>
        <span style="font-family:'Manrope';font-weight:700;color:#c3f5ff;">
          {lowcut:.2f} – {highcut:.0f} Hz</span>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">Baseline</span><br>
        <span style="font-family:'Manrope';font-weight:700;
                     color:{'#c3f400' if remove_bl else '#849396'};">
          {'ON' if remove_bl else 'OFF'}</span>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1rem;display:inline-block;">
        <span style="font-size:0.6rem;color:#849396;font-family:'Inter';
                     text-transform:uppercase;letter-spacing:0.1em;">Extra Filter</span><br>
        <span style="font-family:'Manrope';font-weight:700;color:#c3f5ff;">{noise}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Applying filters…"):
        clean = preprocess_ecg(raw, sfreq, lowcut=lowcut, highcut=highcut,
                               remove_baseline=remove_bl, noise_method=noise)
        if "cleaned_signals" not in st.session_state:
            st.session_state["cleaned_signals"] = {}
        st.session_state["cleaned_signals"][active] = clean

    time_ax = np.arange(len(raw)) / sfreq
    step = max(1, len(raw) // 50000)

    # ── Overlay plot ─────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_ax[::step], y=raw[::step],
        mode='lines', name='Raw',
        line=dict(color=COLORS["outline"], width=1.0),
        opacity=0.55,
        hovertemplate="t=%{x:.3f}s<br>Raw=%{y:.4f}<extra>Raw</extra>"
    ))
    fig.add_trace(go.Scatter(
        x=time_ax[::step], y=clean[::step],
        mode='lines', name='Filtered',
        line=dict(color=COLORS["secondary_fixed"], width=1.8),
        hovertemplate="t=%{x:.3f}s<br>Filtered=%{y:.4f}<extra>Filtered</extra>"
    ))
    layout = {**PLOTLY_LAYOUT}
    layout["title"] = dict(text="Raw vs Filtered ECG", font=dict(family="Manrope", color=COLORS["primary"], size=13))
    layout["xaxis"]["title"] = "Time (s)"
    layout["yaxis"]["title"] = "Amplitude"
    layout["height"] = 480
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True})

    # ── Noise/power comparison panel ─────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Signal Statistics — Raw</div>', unsafe_allow_html=True)
        r = {
            "Mean": f"{np.mean(raw):.4f}",
            "Std Dev": f"{np.std(raw):.4f}",
            "Min": f"{raw.min():.4f}",
            "Max": f"{raw.max():.4f}",
        }
        for k, v in r.items():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
                f'border-bottom:1px solid #1e2023;font-family:Inter;font-size:0.75rem;">'
                f'<span style="color:#849396;">{k}</span>'
                f'<span style="color:#e2e2e6;font-weight:600;">{v}</span></div>',
                unsafe_allow_html=True
            )
    with col2:
        st.markdown('<div class="section-header">Signal Statistics — Filtered</div>', unsafe_allow_html=True)
        c = {
            "Mean": f"{np.mean(clean):.4f}",
            "Std Dev": f"{np.std(clean):.4f}",
            "Min": f"{clean.min():.4f}",
            "Max": f"{clean.max():.4f}",
        }
        for k, v in c.items():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
                f'border-bottom:1px solid #1e2023;font-family:Inter;font-size:0.75rem;">'
                f'<span style="color:#849396;">{k}</span>'
                f'<span style="color:#c3f400;font-weight:600;">{v}</span></div>',
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    main()
