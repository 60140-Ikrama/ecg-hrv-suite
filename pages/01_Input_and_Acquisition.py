"""Dashboard 1 — ECG Input & Signal Acquisition"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.data_loader import load_ecg_file

st.set_page_config(page_title="Acquisition · Clinical Sentinel", page_icon="📡", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "No file loaded")
    sentinel_header("Dashboard 1 · Signal Acquisition", badge="Input", active_file=active)
    pipeline_status_bar("Acquire")

    if "raw_signals" not in st.session_state:
        st.session_state["raw_signals"] = {}

    # ── Upload ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Upload ECG Files</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Supported: .csv  .txt  .dat  .mat  .edf",
        type=["csv", "txt", "dat", "mat", "edf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        progress = st.progress(0, text="Loading files…")
        for i, f in enumerate(uploaded):
            if f.name not in st.session_state["raw_signals"]:
                try:
                    sig, detected_fs, info = load_ecg_file(f)
                    if sig is not None:
                        st.session_state["raw_signals"][f.name] = sig
                        # Auto-detect or store fs
                        if detected_fs and st.session_state.get("auto_sfreq", False):
                            st.session_state["sfreq"] = detected_fs
                        st.toast(f"✅ Loaded {f.name} ({len(sig):,} samples)", icon="📡")
                except Exception as e:
                    st.error(f"❌ {f.name}: {e}")
            progress.progress((i + 1) / len(uploaded), text=f"Loaded {i+1}/{len(uploaded)}")
        progress.empty()

    # ── File selector ───────────────────────────────────────────────────────
    raw = st.session_state.get("raw_signals", {})
    if not raw:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#849396;">
          <div style="font-size:3rem;">📡</div>
          <div style="font-family:'Manrope',sans-serif;font-size:0.9rem;font-weight:700;
                      color:#bac9cc;margin-top:0.5rem;">No ECG data loaded yet</div>
          <div style="font-size:0.75rem;margin-top:0.25rem;">
            Upload one or more ECG files above to begin.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    col_sel, col_info = st.columns([2, 1], gap="medium")
    with col_sel:
        selected = st.selectbox("Active File", list(raw.keys()), label_visibility="collapsed")
        st.session_state["active_file"] = selected

    signal = raw[selected]
    sfreq = st.session_state.get("sfreq", 250.0)
    duration = len(signal) / sfreq

    with col_info:
        st.markdown(f"""
        <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.3rem;">
          <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
            <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter';">Samples</div>
            <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;font-family:'Manrope';">{len(signal):,}</div>
          </div>
          <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
            <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter';">Duration</div>
            <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;font-family:'Manrope';">{duration:.1f}s</div>
          </div>
          <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
            <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;letter-spacing:0.1em;font-family:'Inter';">Fs</div>
            <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;font-family:'Manrope';">{sfreq:.0f} Hz</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Signal plot ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header" style="margin-top:1.2rem;">Raw ECG Signal</div>', unsafe_allow_html=True)
    
    time_ax = np.arange(len(signal)) / sfreq
    step = max(1, len(signal) // 50000)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_ax[::step], y=signal[::step],
        mode='lines', name='Raw ECG',
        line=dict(color=COLORS["outline"], width=1.2),
        hovertemplate="t=%{x:.3f}s  amp=%{y:.4f}<extra>Raw ECG</extra>"
    ))
    layout = {**PLOTLY_LAYOUT}
    layout["title"] = dict(text=f"Raw ECG — {selected}", font=dict(family="Manrope", color=COLORS["primary"], size=13))
    layout["xaxis"]["title"] = "Time (s)"
    layout["yaxis"]["title"] = "Amplitude"
    layout["height"] = 400
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

    # ── Loaded files table ──────────────────────────────────────────────────
    if len(raw) > 1:
        st.markdown('<div class="section-header" style="margin-top:1rem;">Batch Session Files</div>', unsafe_allow_html=True)
        rows = []
        for fname, s in raw.items():
            rows.append({
                "File": fname,
                "Samples": f"{len(s):,}",
                "Duration (s)": f"{len(s)/sfreq:.1f}",
                "Amplitude Range": f"{s.min():.3f} → {s.max():.3f}",
                "Status": "✅ Ready",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
