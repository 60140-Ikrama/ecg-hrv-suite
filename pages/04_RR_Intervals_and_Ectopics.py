"""Dashboards 4 & 5 — RR Interval Analysis & Ectopic Beat Correction"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, kpi_card, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import get_rr_intervals
from utils.hrv_analysis import detect_ectopic_beats, correct_ectopic_beats

st.set_page_config(page_title="RR & Ectopics · Clinical Sentinel", page_icon="⏱️", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboards 4 & 5 · RR Intervals & Ectopic Correction", badge="Critical", active_file=active)
    pipeline_status_bar("Ectopic")

    if not active or active not in st.session_state.get("rpeaks", {}):
        st.warning("⚠️  Run **❤️ R-Peak Detection** first.")
        return

    rpeaks = st.session_state["rpeaks"][active]
    sfreq = st.session_state.get("sfreq", 250.0)
    enable_correction = st.session_state.get("remove_ectopic", True)
    threshold = st.session_state.get("ectopic_threshold", 20) / 100.0
    interp_method = st.session_state.get("ectopic_interp", "Linear")

    raw_rr = get_rr_intervals(rpeaks, sfreq)
    if len(raw_rr) < 3:
        st.error("Not enough R-peaks to compute RR intervals.")
        return

    # Detect and correct
    mask = detect_ectopic_beats(raw_rr, threshold=threshold) if enable_correction else np.zeros(len(raw_rr), dtype=bool)
    clean_rr = correct_ectopic_beats(raw_rr, mask, method=interp_method) if enable_correction else raw_rr.copy()

    n_ectopic = int(np.sum(mask))
    pct_ectopic = n_ectopic / len(raw_rr) * 100

    # Save to state
    if "clean_rr_intervals" not in st.session_state:
        st.session_state["clean_rr_intervals"] = {}
    st.session_state["clean_rr_intervals"][active] = clean_rr

    # ── KPI row ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1.25rem;">
      {kpi_card("Total Beats", str(len(raw_rr)), accent="primary")}
      {kpi_card("Ectopic Detected", str(n_ectopic), accent="amber" if n_ectopic>0 else "primary")}
      {kpi_card("Ectopic Rate", f"{pct_ectopic:.1f}", "%", accent="amber" if pct_ectopic>5 else "green")}
      {kpi_card("Correction", interp_method if enable_correction else "Disabled",
                accent="green" if enable_correction else "amber")}
    </div>
    """, unsafe_allow_html=True)

    # ── Dual tachogram ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">RR Interval Tachogram — Raw vs Corrected</div>', unsafe_allow_html=True)

    beats = np.arange(len(raw_rr))
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.08,
                        subplot_titles=["Raw RR Series", "Corrected RR Series"])

    # Raw trace
    fig.add_trace(go.Scatter(
        x=beats, y=raw_rr, mode='lines',
        name='Raw RR', line=dict(color=COLORS["outline"], width=1.2)),
        row=1, col=1)
    # Ectopic highlights on raw
    if n_ectopic > 0:
        eidx = np.where(mask)[0]
        fig.add_trace(go.Scatter(
            x=eidx, y=raw_rr[eidx], mode='markers',
            name='Ectopic Beats',
            marker=dict(color=COLORS["error"], size=8, symbol='x',
                        line=dict(color='white', width=1))),
            row=1, col=1)

    # Clean trace
    fig.add_trace(go.Scatter(
        x=beats, y=clean_rr, mode='lines',
        name='Clean RR', line=dict(color=COLORS["primary_dim"], width=1.5)),
        row=2, col=1)
    # Interpolated points
    if n_ectopic > 0:
        eidx = np.where(mask)[0]
        fig.add_trace(go.Scatter(
            x=eidx, y=clean_rr[eidx], mode='markers',
            name='Interpolated',
            marker=dict(color=COLORS["secondary_fixed"], size=7,
                        line=dict(color='white', width=1))),
            row=2, col=1)

    lay = {**PLOTLY_LAYOUT}
    lay["height"] = 520
    lay["showlegend"] = True
    lay["title"] = None
    fig.update_layout(**lay)
    fig.update_xaxes(title_text="Beat Number", row=2, col=1, gridcolor=COLORS["outline_variant"])
    fig.update_yaxes(title_text="RR (ms)", gridcolor=COLORS["outline_variant"])
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    # ── Distribution comparison ────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Raw RR Distribution</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=raw_rr, nbinsx=40,
            marker_color=COLORS["outline"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.5),
            name='Raw'
        ))
        lay2 = {**PLOTLY_LAYOUT}
        lay2["height"] = 280
        lay2["xaxis"]["title"] = "RR (ms)"
        lay2["yaxis"]["title"] = "Count"
        lay2["title"] = None
        fig2.update_layout(**lay2)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Clean RR Distribution</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=clean_rr, nbinsx=40,
            marker_color=COLORS["primary_dim"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.5),
            name='Clean'
        ))
        lay3 = {**PLOTLY_LAYOUT}
        lay3["height"] = 280
        lay3["xaxis"]["title"] = "RR (ms)"
        lay3["yaxis"]["title"] = "Count"
        lay3["title"] = None
        fig3.update_layout(**lay3)
        st.plotly_chart(fig3, use_container_width=True)

    # Clinical note
    if pct_ectopic > 10:
        st.markdown("""
        <div class="clinical-card warning">
          <div class="clinical-title">⚠️ High Ectopic Rate Detected</div>
          <div class="clinical-body">
            More than 10% of beats were flagged as ectopic. This may indicate significant
            arrhythmia (e.g., PVC) or noise contamination. Review signal quality and 
            adjust the ectopic threshold in the sidebar.
          </div>
        </div>
        """, unsafe_allow_html=True)
    elif n_ectopic > 0:
        st.markdown(f"""
        <div class="clinical-card success">
          <div class="clinical-title">✅ Ectopic Correction Applied</div>
          <div class="clinical-body">
            {n_ectopic} ectopic beat(s) detected ({pct_ectopic:.1f}%) and corrected
            using <strong>{interp_method}</strong> interpolation. The clean RR series 
            is now ready for HRV analysis.
          </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
