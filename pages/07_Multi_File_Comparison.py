"""Dashboard 10 — Multi-File Comparison: side-by-side HRV, PSD overlay, radar chart"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header,
                               COLORS, get_plot_layout, set_layout)
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="Multi-File Comparison · Clinical Sentinel",
                   page_icon="📁", layout="wide")

PALETTE = ["#00daf3", "#c3f400", "#ffba38", "#ffb4ab",
           "#9cf0ff", "#abd600", "#ffc769", "#cf6679"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe(v):
    """Return float or None; guard NaN."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f != f) else f   # NaN check
    except Exception:
        return None


def _bar_chart(files, metrics_dict, key, label, color_idx_offset=0):
    """Return a compact single-metric bar figure."""
    vals   = [_safe(metrics_dict.get(f, {}).get(key)) for f in files]
    labels = [os.path.splitext(f)[0][:14] for f in files]
    fig    = go.Figure()
    for i, (lbl, val) in enumerate(zip(labels, vals)):
        if val is not None:
            fig.add_trace(go.Bar(
                x=[lbl], y=[val],
                name=lbl,
                marker_color=PALETTE[(i + color_idx_offset) % len(PALETTE)],
                text=[f"{val:.1f}"], textposition="outside",
                textfont=dict(color=COLORS["on_surface_variant"], size=9)))
    set_layout(fig, label, xaxis_title="", yaxis_title=key)
    fig.update_layout(height=290, showlegend=False, margin=dict(l=30, r=10, t=30, b=40))
    return fig


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 10 · Multi-File Comparison", badge="Advanced")
    pipeline_status_bar("HRV")

    metrics_dict = st.session_state.get("metrics", {})
    psd_data     = st.session_state.get("psd_data",  {})
    sqi_cache    = st.session_state.get("sqi_cache",  {})

    if not metrics_dict:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#849396;">
          <div style="font-size:3rem;">📁</div>
          <div style="font-family:'Manrope';font-size:0.9rem;font-weight:700;
                      color:#bac9cc;margin-top:0.5rem;">No analysed files yet</div>
          <div style="font-size:0.75rem;margin-top:0.25rem;">
            Upload and process multiple ECG files through the pipeline, then return here.
          </div>
        </div>""", unsafe_allow_html=True)
        return

    files = list(metrics_dict.keys())
    st.markdown(f"""
    <div style="margin-bottom:1.25rem;">
      <span style="font-family:'Manrope';font-size:0.6rem;font-weight:800;
                   color:#849396;text-transform:uppercase;letter-spacing:0.15em;">
        Comparing</span>
      <span style="font-family:'Manrope';font-size:1.1rem;font-weight:700;
                   color:#c3f5ff;margin-left:0.5rem;">{len(files)} file(s)</span>
    </div>""", unsafe_allow_html=True)

    # ── Full metrics table ────────────────────────────────────────────────────
    section_header("Statistical Summary Table")
    rows = []
    for f in files:
        m   = metrics_dict[f]
        sqi = sqi_cache.get(f, {})
        row = {"File": f}
        row.update(m)
        if sqi:
            row["SQI (overall)"]  = sqi.get("overall_sqi")
            row["Quality Label"]  = sqi.get("quality_label")
            row["SNR (dB)"]       = sqi.get("snr_db")
        rows.append(row)

    df = pd.DataFrame(rows)
    float_cols = df.select_dtypes(include=[float]).columns
    st.dataframe(
        df.style.format({c: "{:.2f}" for c in float_cols}, na_rep="N/A"),
        use_container_width=True, hide_index=True)

    if len(files) < 2:
        st.info("Process at least **2 files** through the full pipeline for comparative charts.")
        return

    # ── Bar comparisons ───────────────────────────────────────────────────────
    section_header("HRV Metrics Side-by-Side")
    compare_keys = [
        ("SDNN (ms)",      "SDNN"),
        ("RMSSD (ms)",     "RMSSD"),
        ("pNN50 (%)",      "pNN50"),
        ("LF/HF Ratio",   "LF/HF"),
        ("SD1 (ms)",       "SD1"),
        ("SD2 (ms)",       "SD2"),
    ]
    # Arrange in rows of 3
    for row_start in range(0, len(compare_keys), 3):
        row_keys = compare_keys[row_start:row_start + 3]
        cols = st.columns(len(row_keys))
        for col, (key, label) in zip(cols, row_keys):
            col.plotly_chart(
                _bar_chart(files, metrics_dict, key, label),
                use_container_width=True)

    # ── Radar / Spider chart ──────────────────────────────────────────────────
    section_header("HRV Radar Chart (Normalised)")
    radar_keys = ["SDNN (ms)", "RMSSD (ms)", "pNN50 (%)",
                  "SD1 (ms)", "SD2 (ms)", "HF norm (%)"]

    # Collect and normalise per metric (0–1)
    radar_vals = {}
    col_maxes  = {}
    for k in radar_keys:
        vals = [_safe(metrics_dict.get(f, {}).get(k)) for f in files]
        vals_clean = [v for v in vals if v is not None]
        col_maxes[k] = max(vals_clean) if vals_clean else 1.0
    for f in files:
        radar_vals[f] = [
            (_safe(metrics_dict.get(f, {}).get(k)) or 0) / max(col_maxes[k], 1e-9)
            for k in radar_keys]

    fig_r = go.Figure()
    for i, f in enumerate(files):
        name = os.path.splitext(f)[0][:20]
        vals_norm = radar_vals[f]
        fig_r.add_trace(go.Scatterpolar(
            r=vals_norm + [vals_norm[0]],          # close the polygon
            theta=radar_keys + [radar_keys[0]],
            fill='toself',
            fillcolor=PALETTE[i % len(PALETTE)].replace("#", "rgba(") + ",0.15)",
            name=name,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2)))

    set_layout(fig_r, "Normalized HRV Metrics (Radar)", xaxis_title="", yaxis_title="")
    fig_r.update_layout(
        polar=dict(
            bgcolor=COLORS["surface_container_lowest"],
            radialaxis=dict(visible=True, range=[0, 1],
                            gridcolor=COLORS["outline_variant"],
                            tickfont=dict(color=COLORS["on_surface_variant"], size=9)),
            angularaxis=dict(gridcolor=COLORS["outline_variant"],
                             tickfont=dict(color=COLORS["on_surface_variant"], size=10))),
        height=460
    )
    st.plotly_chart(fig_r, use_container_width=True)

    # ── PSD Overlay ───────────────────────────────────────────────────────────
    if psd_data and len([f for f in files if f in psd_data]) >= 2:
        section_header("Power Spectral Density Overlay")
        fig_psd = go.Figure()
        for i, f in enumerate(files):
            if f not in psd_data:
                continue
            freqs, psd = psd_data[f]
            color = PALETTE[i % len(PALETTE)]
            fig_psd.add_trace(go.Scatter(
                x=freqs, y=psd, mode='lines',
                name=os.path.splitext(f)[0],
                line=dict(color=color, width=1.8),
                hovertemplate=f"{f}<br>f=%{{x:.3f}} Hz<br>PSD=%{{y:.2f}}<extra></extra>"))

        lf_min = st.session_state.get("lf_min", 0.04)
        lf_max = st.session_state.get("lf_max", 0.15)
        hf_min = st.session_state.get("hf_min", 0.15)
        hf_max = st.session_state.get("hf_max", 0.40)
        fig_psd.add_vrect(x0=lf_min, x1=lf_max,
                          fillcolor="rgba(255,186,56,0.07)", line_width=0,
                          annotation_text="LF",
                          annotation_font=dict(color=COLORS["tertiary_fixed_dim"], size=10))
        fig_psd.add_vrect(x0=hf_min, x1=hf_max,
                          fillcolor="rgba(0,218,243,0.07)", line_width=0,
                          annotation_text="HF",
                          annotation_font=dict(color=COLORS["primary_dim"], size=10))
        set_layout(fig_psd, "PSD Overlay (Welch's Method)", xaxis_title="Frequency (Hz)", yaxis_title="PSD (ms²/Hz)")
        fig_psd.update_layout(xaxis=dict(range=[0, 0.5]), height=400)
        st.plotly_chart(fig_psd, use_container_width=True,
                        config={"scrollZoom": True})

    # ── RMSSD vs HF Power scatter ─────────────────────────────────────────────
    valid = [f for f in files
             if "RMSSD (ms)"     in metrics_dict.get(f, {})
             and "HF Power (ms²)" in metrics_dict.get(f, {})]
    if len(valid) >= 2:
        section_header("Scatter: RMSSD vs HF Power (Parasympathetic Concordance)")
        xs     = [_safe(metrics_dict[f].get("RMSSD (ms)"))      for f in valid]
        ys     = [_safe(metrics_dict[f].get("HF Power (ms²)"))  for f in valid]
        labels = [os.path.splitext(f)[0] for f in valid]
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(valid))]
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers+text',
            text=labels, textposition="top center",
            textfont=dict(color=COLORS["on_surface_variant"], size=9),
            marker=dict(size=14, color=colors,
                        line=dict(color='white', width=1.5))))
        set_layout(fig_s, "RMSSD vs HF Power Concordance", xaxis_title="RMSSD (ms)", yaxis_title="HF Power (ms²)")
        fig_s.update_layout(height=380)
        st.plotly_chart(fig_s, use_container_width=True)

    # ── Statistical delta table ───────────────────────────────────────────────
    if len(files) == 2:
        section_header("Δ Difference Between Files")
        f1, f2 = files[0], files[1]
        delta_rows = []
        for key in ["Mean RR (ms)", "SDNN (ms)", "RMSSD (ms)", "pNN50 (%)",
                    "LF/HF Ratio", "HF Power (ms²)", "SD1 (ms)", "SD2 (ms)",
                    "DFA α1", "DFA α2", "Sample Entropy"]:
            v1 = _safe(metrics_dict.get(f1, {}).get(key))
            v2 = _safe(metrics_dict.get(f2, {}).get(key))
            if v1 is not None and v2 is not None:
                delta = v2 - v1
                pct   = (delta / abs(v1) * 100) if v1 != 0 else float('nan')
                delta_rows.append({
                    "Metric":  key,
                    os.path.splitext(f1)[0][:18]: f"{v1:.2f}",
                    os.path.splitext(f2)[0][:18]: f"{v2:.2f}",
                    "Δ":       f"{delta:+.2f}",
                    "Δ %":     f"{pct:+.1f}%" if abs(pct) < 1000 else "—",
                })
        if delta_rows:
            st.dataframe(pd.DataFrame(delta_rows),
                         use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
