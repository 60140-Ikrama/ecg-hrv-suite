"""Dashboard 3 — R-Peak Detection"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import detect_r_peaks, compute_heart_rate

st.set_page_config(page_title="R-Peak Detection · Clinical Sentinel", page_icon="❤️", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboard 3 · R-Peak Detection", badge="Detect", active_file=active)
    pipeline_status_bar("R-Peaks")

    if not active or active not in st.session_state.get("cleaned_signals", {}):
        st.warning("⚠️  Run **🧹 Preprocessing** first.")
        return

    clean = st.session_state["cleaned_signals"][active]
    sfreq = st.session_state.get("sfreq", 250.0)
    method = st.session_state.get("rpeak_method", "NeuroKit")

    with st.spinner(f"Detecting R-peaks with {method}…"):
        try:
            rpeaks = detect_r_peaks(clean, sfreq, method=method)
            if "rpeaks" not in st.session_state:
                st.session_state["rpeaks"] = {}
            st.session_state["rpeaks"][active] = rpeaks
        except Exception as e:
            st.error(f"Detection failed: {e}")
            return

    hr = compute_heart_rate(rpeaks, sfreq)

    # ── Stats bar ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.25rem;">
      <div class="glass-panel" style="padding:0.5rem 1.1rem;">
        <div style="font-size:0.55rem;color:#849396;font-family:'Inter';text-transform:uppercase;letter-spacing:0.1em;">Algorithm</div>
        <div style="font-family:'Manrope';font-weight:700;color:#c3f5ff;">{method}</div>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1.1rem;">
        <div style="font-size:0.55rem;color:#849396;font-family:'Inter';text-transform:uppercase;letter-spacing:0.1em;">R-Peaks Found</div>
        <div style="font-family:'Manrope';font-weight:700;color:#c3f400;">{len(rpeaks)}</div>
      </div>
      <div class="glass-panel" style="padding:0.5rem 1.1rem;">
        <div style="font-size:0.55rem;color:#849396;font-family:'Inter';text-transform:uppercase;letter-spacing:0.1em;">Mean HR</div>
        <div style="font-family:'Manrope';font-weight:700;color:#ffba38;">{hr:.1f} BPM</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── ECG + peaks overlay ───────────────────────────────────────────────
    time_ax = np.arange(len(clean)) / sfreq
    step = max(1, len(clean) // 50000)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_ax[::step], y=clean[::step],
        mode='lines', name='Clean ECG',
        line=dict(color=COLORS["secondary_fixed"], width=1.5),
        hovertemplate="t=%{x:.3f}s<extra>ECG</extra>"
    ))
    # R-peaks scatter
    rpeak_t = rpeaks / sfreq
    rpeak_amp = clean[rpeaks]
    fig.add_trace(go.Scatter(
        x=rpeak_t, y=rpeak_amp,
        mode='markers', name='R-Peaks',
        marker=dict(
            color=COLORS["tertiary_fixed_dim"], size=7,
            symbol='triangle-up',
            line=dict(color=COLORS["on_primary"], width=1)
        ),
        hovertemplate="t=%{x:.3f}s<br>amp=%{y:.4f}<extra>R-Peak</extra>"
    ))
    layout = {**PLOTLY_LAYOUT}
    layout["title"] = dict(text=f"R-Peak Detection — {method}", font=dict(family="Manrope", color=COLORS["primary"], size=13))
    layout["xaxis"]["title"] = "Time (s)"
    layout["yaxis"]["title"] = "Amplitude"
    layout["height"] = 500
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True})

    # ── Peak interval histogram ───────────────────────────────────────────
    if len(rpeaks) > 2:
        st.markdown('<div class="section-header" style="margin-top:0.5rem;">R-Peak Interval Distribution</div>', unsafe_allow_html=True)
        rr_ms = np.diff(rpeaks) / sfreq * 1000
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=rr_ms, nbinsx=40,
            marker_color=COLORS["primary_dim"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.5),
            name='RR Distribution'
        ))
        layout2 = {**PLOTLY_LAYOUT}
        layout2["title"] = dict(text="RR Interval Histogram (pre-ectopic)", font=dict(family="Manrope", color=COLORS["primary"], size=13))
        layout2["xaxis"]["title"] = "RR Interval (ms)"
        layout2["yaxis"]["title"] = "Count"
        layout2["height"] = 300
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()
