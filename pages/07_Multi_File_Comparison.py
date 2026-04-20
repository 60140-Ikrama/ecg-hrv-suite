"""Dashboard 10 — Multi-File Comparison"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, section_header, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="Multi-File Comparison · Clinical Sentinel", page_icon="📁", layout="wide")

PALETTE = ["#00daf3", "#c3f400", "#ffba38", "#ffb4ab", "#9cf0ff", "#abd600", "#ffc769"]


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 10 · Multi-File Comparison", badge="Advanced")
    pipeline_status_bar("HRV")

    metrics_dict = st.session_state.get("metrics", {})
    psd_data = st.session_state.get("psd_data", {})

    if not metrics_dict:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#849396;">
          <div style="font-size:3rem;">📁</div>
          <div style="font-family:'Manrope';font-size:0.9rem;font-weight:700;color:#bac9cc;margin-top:0.5rem;">
            No analyzed files yet
          </div>
          <div style="font-size:0.75rem;margin-top:0.25rem;">
            Upload and process multiple ECG files through the pipeline, then return here.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    files = list(metrics_dict.keys())
    st.markdown(f"""
    <div style="margin-bottom:1.25rem;">
      <span style="font-family:'Manrope';font-size:0.6rem;font-weight:800;color:#849396;
                   text-transform:uppercase;letter-spacing:0.15em;">Comparing</span>
      <span style="font-family:'Manrope';font-size:1.1rem;font-weight:700;color:#c3f5ff;
                   margin-left:0.5rem;">{len(files)} file(s)</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary table ─────────────────────────────────────────────────────
    section_header("Statistical Summary Table")
    rows = []
    for f in files:
        m = metrics_dict[f]
        row = {"File": f}
        for k, v in m.items():
            row[k] = v
        rows.append(row)
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format(
            {c: "{:.2f}" for c in df.select_dtypes(include=[float]).columns},
            na_rep="N/A"
        ),
        use_container_width=True, hide_index=True
    )

    if len(files) < 2:
        st.info("Upload and process at least 2 files for comparative charts.")
        return

    # ── Bar comparisons ───────────────────────────────────────────────────
    section_header("HRV Metrics Side-by-Side")
    metrics_to_compare = [
        ("SDNN (ms)", "SDNN"),
        ("RMSSD (ms)", "RMSSD"),
        ("pNN50 (%)", "pNN50"),
        ("LF/HF Ratio", "LF/HF"),
    ]
    cols = st.columns(len(metrics_to_compare))
    for col, (key, label) in zip(cols, metrics_to_compare):
        vals = [metrics_dict.get(f, {}).get(key, None) for f in files]
        short_labels = [os.path.splitext(f)[0][:12] for f in files]
        fig = go.Figure()
        for i, (fname, val) in enumerate(zip(short_labels, vals)):
            if val is not None:
                fig.add_trace(go.Bar(
                    x=[fname], y=[val],
                    name=fname,
                    marker_color=PALETTE[i % len(PALETTE)],
                    text=[f"{val:.1f}"], textposition='outside',
                    textfont=dict(color=COLORS["on_surface_variant"], size=9)
                ))
        lay = {**PLOTLY_LAYOUT, "height": 300, "showlegend": False}
        lay["title"] = dict(text=label, font=dict(family="Manrope", color=COLORS["primary"], size=12))
        lay["yaxis"]["title"] = key
        lay["title"] = None
        fig.update_layout(**lay)
        fig.update_layout(title_text=label, title_font=dict(color=COLORS["primary"], size=12, family="Manrope"))
        col.plotly_chart(fig, use_container_width=True)

    # ── PSD Overlay ───────────────────────────────────────────────────────
    if psd_data and len(psd_data) >= 2:
        section_header("Power Spectral Density Overlay")
        fig_psd = go.Figure()
        for i, fname in enumerate(files):
            if fname in psd_data:
                freqs, psd = psd_data[fname]
                color = PALETTE[i % len(PALETTE)]
                fig_psd.add_trace(go.Scatter(
                    x=freqs, y=psd, mode='lines',
                    name=os.path.splitext(fname)[0],
                    line=dict(color=color, width=1.8),
                    hovertemplate=f"{fname}<br>f=%{{x:.3f}} Hz<br>PSD=%{{y:.2f}}<extra></extra>"
                ))

        # Band regions
        lf_min = st.session_state.get("lf_min", 0.04)
        lf_max = st.session_state.get("lf_max", 0.15)
        hf_min = st.session_state.get("hf_min", 0.15)
        hf_max = st.session_state.get("hf_max", 0.40)
        fig_psd.add_vrect(x0=lf_min, x1=lf_max,
                           fillcolor="rgba(255,186,56,0.07)",
                           line_width=0, annotation_text="LF",
                           annotation_font=dict(color=COLORS["tertiary_fixed_dim"], size=10))
        fig_psd.add_vrect(x0=hf_min, x1=hf_max,
                           fillcolor="rgba(0,218,243,0.07)",
                           line_width=0, annotation_text="HF",
                           annotation_font=dict(color=COLORS["primary_dim"], size=10))

        lay_psd = {**PLOTLY_LAYOUT, "height": 400}
        lay_psd["xaxis"]["title"] = "Frequency (Hz)"
        lay_psd["xaxis"]["range"] = [0, 0.5]
        lay_psd["yaxis"]["title"] = "PSD (ms²/Hz)"
        lay_psd["title"] = None
        fig_psd.update_layout(**lay_psd)
        st.plotly_chart(fig_psd, use_container_width=True, config={"scrollZoom": True})

    # ── Scatter: RMSSD vs HF Power ────────────────────────────────────────
    valid_files = [f for f in files if "RMSSD (ms)" in metrics_dict.get(f, {}) and "HF Power (ms²)" in metrics_dict.get(f, {})]
    if len(valid_files) >= 2:
        section_header("Scatter: RMSSD vs HF Power (Parasympathetic Concordance)")
        xs = [metrics_dict[f].get("RMSSD (ms)", 0) for f in valid_files]
        ys = [metrics_dict[f].get("HF Power (ms²)", 0) for f in valid_files]
        labels = [os.path.splitext(f)[0] for f in valid_files]
        colors_list = [PALETTE[i % len(PALETTE)] for i in range(len(valid_files))]
        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=xs, y=ys, mode='markers+text',
            text=labels, textposition="top center",
            textfont=dict(color=COLORS["on_surface_variant"], size=9),
            marker=dict(size=14, color=colors_list,
                        line=dict(color='white', width=1))
        ))
        lay_sc = {**PLOTLY_LAYOUT, "height": 380}
        lay_sc["xaxis"]["title"] = "RMSSD (ms)"
        lay_sc["yaxis"]["title"] = "HF Power (ms²)"
        lay_sc["title"] = None
        fig_sc.update_layout(**lay_sc)
        st.plotly_chart(fig_sc, use_container_width=True)


if __name__ == "__main__":
    main()
