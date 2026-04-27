"""Dashboards 4 & 5 — RR Interval Analysis, Ectopic Correction & Anomaly Detection"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, kpi_card, section_header,
                               COLORS, get_plot_layout, set_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import get_rr_intervals
from utils.hrv_analysis import (detect_ectopic_beats, correct_ectopic_beats,
                                 detect_anomalies)

st.set_page_config(page_title="RR & Ectopics · Clinical Sentinel",
                   page_icon="⏱️", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboards 4 & 5 · RR Intervals & Ectopic Correction",
                    badge="Critical", active_file=active)
    pipeline_status_bar("Ectopic")

    if not active or active not in st.session_state.get("rpeaks", {}):
        st.warning("⚠️  Run **❤️ R-Peak Detection** first.")
        return

    rpeaks       = st.session_state["rpeaks"][active]
    sfreq        = st.session_state.get("sfreq",             250.0)
    enable_corr  = st.session_state.get("remove_ectopic",    True)
    threshold    = st.session_state.get("ectopic_threshold", 20) / 100.0
    interp_m     = st.session_state.get("ectopic_interp",    "Linear")
    det_method   = st.session_state.get("ectopic_method",    "median")
    anomaly_z    = st.session_state.get("anomaly_z",         3.0)

    raw_rr = get_rr_intervals(rpeaks, sfreq)
    if len(raw_rr) < 3:
        st.error("Not enough R-peaks to compute RR intervals.")
        return

    mask     = (detect_ectopic_beats(raw_rr, threshold=threshold, method=det_method)
                if enable_corr else np.zeros(len(raw_rr), dtype=bool))
    clean_rr = (correct_ectopic_beats(raw_rr, mask, method=interp_m)
                if enable_corr else raw_rr.copy())
    anomalies = detect_anomalies(clean_rr, z_threshold=anomaly_z)

    n_ectopic   = int(np.sum(mask))
    pct_ectopic = n_ectopic / len(raw_rr) * 100
    n_anomaly   = len(anomalies["indices"])

    # Store clean and raw RR
    if "clean_rr_intervals" not in st.session_state:
        st.session_state["clean_rr_intervals"] = {}
    if "raw_rr_intervals" not in st.session_state:
        st.session_state["raw_rr_intervals"] = {}
        
    st.session_state["clean_rr_intervals"][active] = clean_rr
    st.session_state["raw_rr_intervals"][active] = raw_rr

    # ── KPI row ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
      {kpi_card("Total Beats",      str(len(raw_rr)),           accent="primary")}
      {kpi_card("Ectopic Detected", str(n_ectopic),
                accent="amber" if n_ectopic > 0 else "primary")}
      {kpi_card("Ectopic Rate",     f"{pct_ectopic:.1f}", "%",
                accent="amber" if pct_ectopic > 5 else "green")}
      {kpi_card("Anomalies (z>{anomaly_z:.0f})", str(n_anomaly),
                accent="amber" if n_anomaly > 0 else "green")}
      {kpi_card("Correction",       interp_m if enable_corr else "Disabled",
                accent="green" if enable_corr else "amber")}
    </div>
    """, unsafe_allow_html=True)

    # ── Dual tachogram ────────────────────────────────────────────────────────
    section_header("RR Tachogram — Raw vs Corrected")
    beats = np.arange(len(raw_rr))
    fig   = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          vertical_spacing=0.08,
                          subplot_titles=["Raw RR Series", "Corrected RR Series"])

    fig.add_trace(go.Scatter(x=beats, y=raw_rr / 1000.0, mode='lines', name='Raw RR',
                              line=dict(color=COLORS["outline"], width=1.2)),
                  row=1, col=1)
    if n_ectopic > 0:
        eidx = np.where(mask)[0]
        fig.add_trace(go.Scatter(
            x=eidx, y=raw_rr[eidx] / 1000.0, mode='markers', name='Ectopic',
            marker=dict(color=COLORS["error"], size=9, symbol='x',
                        line=dict(color='white', width=1.5))),
            row=1, col=1)

    fig.add_trace(go.Scatter(x=beats, y=clean_rr / 1000.0, mode='lines', name='Clean RR',
                              line=dict(color=COLORS["primary_dim"], width=1.5)),
                  row=2, col=1)
    if n_ectopic > 0:
        fig.add_trace(go.Scatter(
            x=eidx, y=clean_rr[eidx] / 1000.0, mode='markers', name='Interpolated',
            marker=dict(color=COLORS["secondary_fixed"], size=7,
                        line=dict(color='white', width=1))),
            row=2, col=1)

    set_layout(fig, "RR Tachogram", xaxis_title="Beat Number", yaxis_title="RR (s)")
    fig.update_layout(height=500, showlegend=True)
    fig.update_yaxes(gridcolor=COLORS["outline_variant"])
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    # ── Anomaly z-score plot ───────────────────────────────────────────────────
    section_header("Anomaly Z-Score Analysis")
    z_scores = anomalies["z_scores"]
    if len(z_scores) > 0:
        fig_z = go.Figure()
        colors_z = np.where(np.abs(z_scores) > anomaly_z,
                            COLORS["error"], COLORS["primary_dim"])
        fig_z.add_trace(go.Bar(
            x=beats, y=z_scores, name='Z-Score',
            marker_color=colors_z,
            hovertemplate="Beat %{x}<br>Z = %{y:.2f}<extra></extra>"))
        fig_z.add_hline(y= anomaly_z, line_dash="dot",
                        line_color=COLORS["error"],
                        annotation_text=f"+{anomaly_z}σ",
                        annotation_font=dict(color=COLORS["error"], size=10))
        fig_z.add_hline(y=-anomaly_z, line_dash="dot",
                        line_color=COLORS["error"],
                        annotation_text=f"−{anomaly_z}σ",
                        annotation_font=dict(color=COLORS["error"], size=10))
        set_layout(fig_z, "Z-Score Anomaly Distribution", xaxis_title="Beat Number", yaxis_title="Z-Score")
        fig_z.update_layout(height=280)
        st.plotly_chart(fig_z, use_container_width=True)

        if n_anomaly > 0:
            import pandas as pd
            anom_df = pd.DataFrame({
                "Beat": anomalies["indices"],
                "RR (ms)": [f"{clean_rr[i]:.1f}" for i in anomalies["indices"]],
                "Z-Score": [f"{z_scores[i]:.2f}" for i in anomalies["indices"]],
                "Classification": anomalies["types"],
            })
            st.dataframe(anom_df, use_container_width=True, hide_index=True)

    # ── Distribution comparison ────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    for col, arr, lbl, color in [
        (col1, raw_rr / 1000.0,   "Raw RR",   COLORS["outline"]),
        (col2, clean_rr / 1000.0, "Clean RR", COLORS["primary_dim"]),
    ]:
        with col:
            section_header(f"{lbl} Distribution")
            fh = go.Figure()
            fh.add_trace(go.Histogram(
                x=arr, nbinsx=40, name=lbl,
                marker_color=color,
                marker_line=dict(color=COLORS["outline_variant"], width=0.5)))
            set_layout(fh, f"{lbl} Histogram", xaxis_title="RR (s)", yaxis_title="Count")
            fh.update_layout(height=260)
            st.plotly_chart(fh, use_container_width=True)

    # ── Clinical notes ────────────────────────────────────────────────────────
    if pct_ectopic > 10:
        st.markdown("""
        <div class="clinical-card warning">
          <div class="clinical-title">⚠️ High Ectopic Rate</div>
          <div class="clinical-body">
            >10% of beats flagged as ectopic. May indicate significant arrhythmia (PVC)
            or noise contamination. Review signal quality and lower the threshold.
          </div>
        </div>""", unsafe_allow_html=True)
    elif n_ectopic > 0:
        st.markdown(f"""
        <div class="clinical-card success">
          <div class="clinical-title">✅ Ectopic Correction Applied</div>
          <div class="clinical-body">
            {n_ectopic} ectopic beat(s) ({pct_ectopic:.1f}%) corrected via
            <strong>{interp_m}</strong> interpolation using <strong>{det_method}</strong> detection.
            Clean RR series is ready for HRV analysis.
          </div>
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
