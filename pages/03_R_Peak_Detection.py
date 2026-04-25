"""Dashboard 3 — R-Peak Detection with multi-method comparison"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header,
                               kpi_card, COLORS, get_plot_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.rpeak_detection import (detect_r_peaks, compare_r_peak_methods,
                                    compute_agreement, compute_heart_rate,
                                    get_rr_intervals)

st.set_page_config(page_title="R-Peak Detection · Clinical Sentinel",
                   page_icon="❤️", layout="wide")

PALETTE = ["#00daf3", "#c3f400", "#ffba38", "#ffb4ab", "#9cf0ff"]


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboard 3 · R-Peak Detection", badge="Detect", active_file=active)
    pipeline_status_bar("R-Peaks")

    if not active or active not in st.session_state.get("cleaned_signals", {}):
        st.warning("⚠️  Run **🧹 Preprocessing** first.")
        return

    clean  = st.session_state["cleaned_signals"][active]
    sfreq  = st.session_state.get("sfreq",        250.0)
    method = st.session_state.get("rpeak_method", "NeuroKit")

    # ── Primary detection ─────────────────────────────────────────────────────
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

    # ── Stats bar ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
      {kpi_card("Algorithm",   method,           accent="primary")}
      {kpi_card("R-Peaks",     str(len(rpeaks)), accent="green")}
      {kpi_card("Mean HR",     f"{hr:.1f}", "bpm", accent="amber")}
    </div>
    """, unsafe_allow_html=True)

    # ── ECG + peaks overlay ────────────────────────────────────────────────────
    section_header("ECG with Detected R-Peaks")
    t    = np.arange(len(clean)) / sfreq
    step = max(1, len(clean) // 50_000)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t[::step], y=clean[::step], mode='lines', name='Clean ECG',
        line=dict(color=COLORS["secondary_fixed"], width=1.5),
        hovertemplate="t=%{x:.3f}s<extra>ECG</extra>"))
    fig.add_trace(go.Scatter(
        x=rpeaks / sfreq, y=clean[rpeaks], mode='markers', name='R-Peaks',
        marker=dict(color=COLORS["tertiary_fixed_dim"], size=8,
                    symbol='triangle-up',
                    line=dict(color=COLORS["on_primary"], width=1)),
        hovertemplate="t=%{x:.3f}s<br>amp=%{y:.4f}<extra>R-Peak</extra>"))
    lay = get_plot_layout()
    lay["title"]  = dict(text=f"R-Peak Detection — {method}",
                          font=dict(family="Manrope", color=COLORS["primary"], size=13))
    lay["xaxis"]["title"] = "Time (s)"
    lay["yaxis"]["title"] = "Amplitude"
    lay["height"] = 460
    fig.update_layout(**lay)
    st.plotly_chart(fig, use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True})

    # ── Multi-method comparison ────────────────────────────────────────────────
    section_header("Multi-Method Comparison (CLO1 Demonstration)")
    compare_methods = ["Pan-Tompkins (Custom)", "NeuroKit", "Pan-Tompkins", "Hamilton"]

    with st.spinner("Running all detection methods…"):
        results = compare_r_peak_methods(clean, sfreq, methods=compare_methods)

    # Agreement vs primary method
    primary_rp = rpeaks
    rows = []
    for m, res in results.items():
        rp = res["rpeaks"]
        agr = compute_agreement(primary_rp, rp, sfreq=sfreq) if len(rp) else 0.0
        rows.append({
            "Method":          m,
            "R-Peaks":         res["count"],
            "Mean HR (bpm)":   res["mean_hr"],
            f"Agreement vs {method} (%)": agr,
            "Status":          "✅ OK" if "error" not in res else f"⚠️ {res['error'][:40]}",
        })

    df_cmp = pd.DataFrame(rows)
    st.dataframe(df_cmp.style.format({
        f"Agreement vs {method} (%)": "{:.1f}",
        "Mean HR (bpm)": "{:.1f}",
    }), use_container_width=True, hide_index=True)

    # ── Overlay of all methods ─────────────────────────────────────────────────
    section_header("All Methods — Peak Position Overlay")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=t[::step], y=clean[::step], mode='lines', name='ECG',
        line=dict(color=COLORS["outline_variant"], width=1.0), opacity=0.7))

    for i, (m, res) in enumerate(results.items()):
        rp = res["rpeaks"]
        if len(rp) == 0:
            continue
        color = PALETTE[i % len(PALETTE)]
        fig2.add_trace(go.Scatter(
            x=rp / sfreq, y=clean[rp], mode='markers',
            name=m,
            marker=dict(color=color, size=6, opacity=0.85,
                        symbol=['triangle-up', 'circle', 'square', 'diamond'][i % 4],
                        line=dict(color='white', width=0.5)),
            hovertemplate=f"{m}<br>t=%{{x:.3f}}s<extra></extra>"))

    lay2 = get_plot_layout()
    lay2["title"]  = dict(text="")
    lay2["height"] = 360
    lay2["xaxis"]["title"] = "Time (s)"
    lay2["yaxis"]["title"] = "Amplitude"
    fig2.update_layout(**lay2)
    st.plotly_chart(fig2, use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True})

    # ── RR histogram ─────────────────────────────────────────────────────────
    if len(rpeaks) > 2:
        section_header("RR Interval Distribution (pre-ectopic)")
        rr_ms = get_rr_intervals(rpeaks, sfreq)
        fig3 = go.Figure()
        fig3.add_trace(go.Histogram(
            x=rr_ms, nbinsx=40,
            marker_color=COLORS["primary_dim"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.5),
            name='RR Distribution'))
        lay3 = get_plot_layout()
        lay3["title"]  = dict(text="")
        lay3["height"] = 280
        lay3["xaxis"]["title"] = "RR Interval (ms)"
        lay3["yaxis"]["title"] = "Count"
        fig3.update_layout(**lay3)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Pan-Tompkins CLO1 explanation ─────────────────────────────────────────
    with st.expander("📚 Pan-Tompkins Algorithm — CLO1 Implementation Detail"):
        st.markdown("""
**Custom Pan-Tompkins (1985) — from-scratch implementation:**

| Step | Operation | Purpose |
|---|---|---|
| 1 | Butterworth bandpass **5–15 Hz** | Isolates QRS energy, rejects baseline & HF noise |
| 2 | Five-point derivative | Emphasises steep QRS slope; suppresses P/T waves |
| 3 | Point-wise squaring | Makes all values positive; amplifies large slopes |
| 4 | Moving-window integration **(150 ms)** | Produces smooth envelope over QRS complex |
| 5 | Adaptive dual-threshold | Learns SPKI/NPKI on-line; handles varying amplitudes |
| 6 | Back-projection ± 50 ms | Finds true R-peak in raw ECG for sub-sample accuracy |

**Adaptive thresholds:**
- `THRESHOLD_I1 = NPKI + 0.25 × (SPKI − NPKI)`  — primary gate
- `THRESHOLD_I2 = 0.5 × THRESHOLD_I1`  — searchback (missed beat) gate
        """)


if __name__ == "__main__":
    main()
