"""Dashboard 1 — ECG Input & Signal Acquisition with Signal Quality Index"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, kpi_card, COLORS, get_plot_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.data_loader import load_ecg_file
from utils.signal_processing import compute_sqi

st.set_page_config(page_title="Acquisition · Clinical Sentinel",
                   page_icon="📡", layout="wide")


def _sqi_badge(label: str, score: float) -> str:
    color = ("#c3f400" if label == "Excellent" else
             "#00daf3" if label == "Good" else
             "#ffba38" if label == "Acceptable" else "#ffb4ab")
    return (f'<span style="background:{color};color:#000;font-family:Manrope;'
            f'font-size:0.65rem;font-weight:800;padding:0.2rem 0.55rem;'
            f'border-radius:0.2rem;text-transform:uppercase;letter-spacing:0.06em;">'
            f'{label} · {score:.0f}</span>')


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "No file loaded")
    sentinel_header("Dashboard 1 · Signal Acquisition", badge="Input", active_file=active)
    pipeline_status_bar("Acquire")

    if "raw_signals" not in st.session_state:
        st.session_state["raw_signals"] = {}
    if "sqi_cache" not in st.session_state:
        st.session_state["sqi_cache"] = {}

    # ── Upload ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Upload ECG Files</div>',
                unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Supported: .csv  .txt  .dat  .mat  .edf",
        type=["csv", "txt", "dat", "mat", "edf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        prog = st.progress(0, text="Loading files…")
        for i, f in enumerate(uploaded):
            if f.name not in st.session_state["raw_signals"]:
                try:
                    sig_arr, det_fs, info = load_ecg_file(f)
                    if sig_arr is not None:
                        st.session_state["raw_signals"][f.name] = sig_arr
                        if det_fs and st.session_state.get("auto_sfreq"):
                            st.session_state["sfreq"] = det_fs
                        # Compute SQI immediately
                        sfreq = st.session_state.get("sfreq", 250.0)
                        st.session_state["sqi_cache"][f.name] = compute_sqi(sig_arr, sfreq)
                        st.toast(f"✅ {f.name}  ({len(sig_arr):,} samples)", icon="📡")
                except Exception as e:
                    st.error(f"❌ {f.name}: {e}")
            prog.progress((i + 1) / len(uploaded), text=f"Loaded {i+1}/{len(uploaded)}")
        prog.empty()

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

    # ── File selector ────────────────────────────────────────────────────────
    col_sel, col_sqi = st.columns([2, 2], gap="medium")
    with col_sel:
        selected = st.selectbox("Active File", list(raw.keys()),
                                label_visibility="collapsed")
        st.session_state["active_file"] = selected

    signal = raw[selected]
    sfreq  = st.session_state.get("sfreq", 250.0)

    # Recompute SQI if not cached
    if selected not in st.session_state["sqi_cache"]:
        st.session_state["sqi_cache"][selected] = compute_sqi(signal, sfreq)
    sqi = st.session_state["sqi_cache"][selected]

    with col_sqi:
        st.markdown(
            f'<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-top:0.3rem;'
            f'align-items:center;">'
            f'<span style="font-size:0.6rem;color:#849396;font-family:Inter;'
            f'text-transform:uppercase;letter-spacing:0.1em;">Signal Quality</span>'
            f'{_sqi_badge(sqi["quality_label"], sqi["overall_sqi"])}'
            f'<span style="font-size:0.7rem;color:#849396;font-family:Inter;">'
            f'SNR {sqi["snr_db"]:.1f} dB</span></div>',
            unsafe_allow_html=True)

    # ── Info chips ───────────────────────────────────────────────────────────
    duration = len(signal) / sfreq
    st.markdown(f"""
    <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.6rem;margin-bottom:0.4rem;">
      <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
        <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;
                    letter-spacing:0.1em;font-family:'Inter';">Samples</div>
        <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;
                    font-family:'Manrope';">{len(signal):,}</div>
      </div>
      <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
        <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;
                    letter-spacing:0.1em;font-family:'Inter';">Duration</div>
        <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;
                    font-family:'Manrope';">{duration:.1f} s</div>
      </div>
      <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
        <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;
                    letter-spacing:0.1em;font-family:'Inter';">Fs</div>
        <div style="font-size:0.95rem;font-weight:700;color:#c3f5ff;
                    font-family:'Manrope';">{sfreq:.0f} Hz</div>
      </div>
      <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
        <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;
                    letter-spacing:0.1em;font-family:'Inter';">Spectral SQI</div>
        <div style="font-size:0.95rem;font-weight:700;color:#ffba38;
                    font-family:'Manrope';">{sqi["spectral_sqi"]:.1f}%</div>
      </div>
      <div style="background:#1e2023;border-radius:0.25rem;padding:0.5rem 0.9rem;">
        <div style="font-size:0.55rem;color:#849396;text-transform:uppercase;
                    letter-spacing:0.1em;font-family:'Inter';">Kurtosis SQI</div>
        <div style="font-size:0.95rem;font-weight:700;color:#c3f400;
                    font-family:'Manrope';">{sqi["kurtosis_sqi"]:.1f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Raw ECG plot ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header" style="margin-top:0.8rem;">Raw ECG Signal</div>',
                unsafe_allow_html=True)
    t  = np.arange(len(signal)) / sfreq
    step = max(1, len(signal) // 50_000)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t[::step], y=signal[::step], mode='lines', name='Raw ECG',
        line=dict(color=COLORS["outline"], width=1.2),
        hovertemplate="t=%{x:.3f}s  amp=%{y:.4f}<extra>Raw ECG</extra>"))
    layout = get_plot_layout()
    layout["title"]  = dict(text=f"Raw ECG — {selected}",
                             font=dict(family="Manrope", color=COLORS["primary"], size=13))
    layout["xaxis"]["title"] = "Time (s)"
    layout["yaxis"]["title"] = "Amplitude"
    layout["height"] = 400
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": True, "scrollZoom": True})

    # ── SQI detail panel ─────────────────────────────────────────────────────
    with st.expander("🔍 Signal Quality Detail"):
        c1, c2, c3 = st.columns(3)
        items = [
            (c1, "Spectral SQI",  sqi["spectral_sqi"],  "QRS-band energy fraction"),
            (c2, "Kurtosis SQI",  sqi["kurtosis_sqi"],  "Peakedness of QRS spikes"),
            (c3, "Baseline SQI",  sqi["baseline_sqi"],  "Absence of baseline drift"),
        ]
        for col, lbl, val, desc in items:
            with col:
                st.metric(lbl, f"{val:.1f} / 100")
                st.caption(desc)

    # ── Batch table ──────────────────────────────────────────────────────────
    if len(raw) > 1:
        st.markdown('<div class="section-header" style="margin-top:1rem;">Batch Session</div>',
                    unsafe_allow_html=True)
        import pandas as pd
        rows = []
        for fname, s in raw.items():
            q = st.session_state["sqi_cache"].get(fname, {})
            rows.append({
                "File": fname,
                "Samples": f"{len(s):,}",
                "Duration (s)": f"{len(s)/sfreq:.1f}",
                "SQI": f"{q.get('overall_sqi', '—'):.0f}" if q else "—",
                "Quality": q.get("quality_label", "—") if q else "—",
                "Amplitude Range": f"{s.min():.3f} → {s.max():.3f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
