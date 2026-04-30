"""Dashboards 6 & 7 — Time-Domain HRV with trend + Frequency-Domain HRV"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, kpi_card, section_header,
                               clinical_interpretation, COLORS, get_plot_layout, set_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import (get_time_domain_hrv, get_freq_domain_hrv,
                                 interpret_hrv, analyze_hrv_trend)

st.set_page_config(page_title="HRV Analysis · Clinical Sentinel",
                   page_icon="📈", layout="wide")


def _safe_band_fill(fig, freqs, psd, idx, fill_color, line_color, name):
    """Add a filled PSD band trace — guards against empty band arrays."""
    if np.sum(idx) < 2:
        return
    fx, py = freqs[idx], psd[idx]
    fig.add_trace(go.Scatter(
        x=np.concatenate([[fx[0]], fx, [fx[-1]]]),
        y=np.concatenate([[0],     py, [0]]),
        fill='toself', fillcolor=fill_color,
        line=dict(color=line_color, width=1.5), name=name))


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboards 6 & 7 · HRV Analysis", badge="HRV", active_file=active)
    pipeline_status_bar("HRV")

    if not active or active not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("⚠️  Process RR intervals in **⏱️ RR & Ectopics** first.")
        return

    # Get confidence multiplier from SQI
    sqi_cache = st.session_state.get("sqi_cache", {}).get(active, {})
    conf_mult = sqi_cache.get("confidence_multiplier", 1.0)
    conf_score = round(conf_mult * 100, 1)

    clean_rr = st.session_state["clean_rr_intervals"][active]
    tab1, tab2 = st.tabs(["📈 Dashboard 6 · Time Domain",
                           "📊 Dashboard 7 · Frequency Domain"])

    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        time_m = get_time_domain_hrv(clean_rr, confidence_multiplier=conf_mult)

        if "metrics" not in st.session_state:
            st.session_state["metrics"] = {}
        if active not in st.session_state["metrics"]:
            st.session_state["metrics"][active] = {}
        st.session_state["metrics"][active].update(time_m)

        # KPI grid
        sdnn_pct  = min(int(time_m.get("SDNN (ms)",  0)), 150)
        rmssd_pct = min(int(time_m.get("RMSSD (ms)", 0)), 100)
        pnn50_pct = min(int(time_m.get("pNN50 (%)",  0)), 100)
        cv_pct    = min(int(time_m.get("CV (%)",     0) * 5), 100)
        
        conf_color = "#c3f400" if conf_score >= 80 else "#ffba38" if conf_score >= 50 else "#ff4b4b"

        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;margin-bottom:0.5rem;">
          <div style="background:{conf_color}22;border:1px solid {conf_color};color:{conf_color};
                      padding:0.2rem 0.6rem;border-radius:1rem;font-size:0.7rem;font-weight:700;">
            🛡️ Analysis Confidence: {conf_score}%
          </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.75rem;margin-bottom:0.75rem;">
          {kpi_card("Mean RR", f"{time_m.get('Mean RR (ms)',0):.0f}", "ms",
                    accent="primary", bar_pct=60)}
          {kpi_card("Mean HR", f"{time_m.get('Mean HR (bpm)',0):.0f}", "bpm",
                    accent="primary")}
          {kpi_card("SDNN",    f"{time_m.get('SDNN (ms)',0):.1f}",    "ms",
                    accent="green", bar_pct=sdnn_pct)}
          {kpi_card("CV",      f"{time_m.get('CV (%)',0):.2f}",       "%",
                    accent="green", bar_pct=cv_pct)}
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
          {kpi_card("RMSSD",   f"{time_m.get('RMSSD (ms)',0):.1f}",  "ms",
                    accent="primary", bar_pct=rmssd_pct)}
          {kpi_card("SDSD",    f"{time_m.get('SDSD (ms)',0):.1f}",   "ms",
                    accent="primary")}
          {kpi_card("NN50",    str(time_m.get("NN50", 0)), "beats",
                    accent="amber")}
          {kpi_card("pNN50",   f"{time_m.get('pNN50 (%)',0):.1f}",   "%",
                    accent="green", bar_pct=pnn50_pct)}
        </div>
        """, unsafe_allow_html=True)

        # |ΔRR| bar chart
        section_header("Successive RR Differences (|ΔRR|)")
        diff_rr = np.abs(np.diff(clean_rr))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=np.arange(len(diff_rr)), y=diff_rr, name='|ΔRR|',
            marker_color=COLORS["primary_dim"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.3),
            hovertemplate="Beat %{x}<br>|ΔRR|=%{y:.1f} ms<extra></extra>"))
        fig.add_hline(y=50, line_dash="dot", line_color=COLORS["secondary_fixed"],
                      annotation_text="NN50 threshold (50 ms)",
                      annotation_font=dict(color=COLORS["secondary_fixed"], size=10))
        set_layout(fig, "Successive RR Differences (|ΔRR|)", xaxis_title="Beat Number", yaxis_title="|ΔRR| (ms)")
        fig.update_layout(height=280)
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        # ── HRV Trend (sliding window) ────────────────────────────────────────
        section_header("HRV Trend Analysis (Sliding Window)")
        trend = analyze_hrv_trend(clean_rr, window_beats=60, step_beats=20)
        if len(trend["beat_centers"]) >= 2:
            fig_t = go.Figure()
            fig_t.add_trace(go.Scatter(
                x=trend["beat_centers"], y=trend["sdnn"],
                mode='lines+markers', name='SDNN',
                line=dict(color=COLORS["secondary_fixed"], width=2),
                marker=dict(size=5)))
            fig_t.add_trace(go.Scatter(
                x=trend["beat_centers"], y=trend["rmssd"],
                mode='lines+markers', name='RMSSD',
                line=dict(color=COLORS["primary_dim"], width=2),
                marker=dict(size=5)))
            set_layout(fig_t, "HRV Trend Analysis (SDNN / RMSSD)", xaxis_title="Beat Centre", yaxis_title="ms")
            fig_t.update_layout(height=260)
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("Need ≥ 60 beats for trend analysis.")

        # Clinical card
        interp = interpret_hrv(time_m, st.session_state["metrics"].get(active, {}))
        st.markdown(f"""
        <div class="clinical-card" style="margin-top:0.75rem;">
          <div class="clinical-title">💡 Time-Domain Clinical Assessment</div>
          <div class="clinical-body">
            <strong>SDNN:</strong> {interp.get("sdnn_class","—")}<br>
            <strong>Vagal Tone (RMSSD):</strong> {interp.get("autonomic","—")}
          </div>
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        lf_band  = (st.session_state.get("lf_min", 0.04),
                    st.session_state.get("lf_max", 0.15))
        hf_band  = (st.session_state.get("hf_min", 0.15),
                    st.session_state.get("hf_max", 0.40))
        vlf_band = (0.003, lf_band[0])
        nperseg  = st.session_state.get("welch_nperseg", 256)
        noverlap = st.session_state.get("welch_noverlap", 128)

        freq_m, freqs, psd = get_freq_domain_hrv(
            clean_rr, vlf_band=vlf_band, lf_band=lf_band, hf_band=hf_band,
            nperseg=nperseg, noverlap=noverlap, confidence_multiplier=conf_mult)

        if freq_m is None:
            st.warning("Not enough RR data for frequency analysis (need > 10 beats).")
            return

        st.session_state["metrics"][active].update(freq_m)
        if "psd_data" not in st.session_state:
            st.session_state["psd_data"] = {}
        st.session_state["psd_data"][active] = (freqs, psd)

        lf_hf     = freq_m.get("LF/HF Ratio", 0)
        lf_hf_str = f"{lf_hf:.2f}" if lf_hf == lf_hf else "N/A"

        # KPI row
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
          {kpi_card("VLF Power", f"{freq_m.get('VLF Power (ms²)',0):.1f}", "ms²", accent="primary")}
          {kpi_card("LF Power",  f"{freq_m.get('LF Power (ms²)',0):.1f}",  "ms²", accent="amber")}
          {kpi_card("HF Power",  f"{freq_m.get('HF Power (ms²)',0):.1f}",  "ms²", accent="primary")}
          {kpi_card("LF/HF",     lf_hf_str,
                    accent="amber" if isinstance(lf_hf, float) and lf_hf > 2 else "green")}
          {kpi_card("Total Power", f"{freq_m.get('Total Power (ms²)',0):.0f}", "ms²", accent="primary")}
        </div>
        """, unsafe_allow_html=True)

        # Band power table
        section_header("Band Power Summary")
        import pandas as pd
        bp_df = pd.DataFrame([
            {"Band": "VLF (0.003–{:.2f} Hz)".format(lf_band[0]),
             "Power (ms²)": freq_m.get("VLF Power (ms²)", 0),
             "% of Total": round(freq_m.get("VLF Power (ms²)", 0) /
                                  max(freq_m.get("Total Power (ms²)", 1), 1) * 100, 1)},
            {"Band": "LF ({:.2f}–{:.2f} Hz)".format(*lf_band),
             "Power (ms²)": freq_m.get("LF Power (ms²)", 0),
             "% of Total": freq_m.get("LF norm (%)", 0)},
            {"Band": "HF ({:.2f}–{:.2f} Hz)".format(*hf_band),
             "Power (ms²)": freq_m.get("HF Power (ms²)", 0),
             "% of Total": freq_m.get("HF norm (%)", 0)},
        ])
        st.dataframe(bp_df.style.format({"Power (ms²)": "{:.2f}", "% of Total": "{:.1f}"}),
                     use_container_width=True, hide_index=True)

        # PSD plot
        section_header("Power Spectral Density (Welch's Method)")
        idx_vlf = (freqs >= vlf_band[0]) & (freqs < vlf_band[1])
        idx_lf  = (freqs >= lf_band[0])  & (freqs < lf_band[1])
        idx_hf  = (freqs >= hf_band[0])  & (freqs < hf_band[1])

        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(
            x=freqs, y=psd, mode='lines', name='PSD',
            line=dict(color=COLORS["on_surface_variant"], width=1.5)))
        _safe_band_fill(fig_p, freqs, psd, idx_vlf,
                        'rgba(132,147,150,0.15)', COLORS["outline_variant"],   'VLF')
        _safe_band_fill(fig_p, freqs, psd, idx_lf,
                        'rgba(255,186,56,0.25)',  COLORS["tertiary_fixed_dim"], 'LF')
        _safe_band_fill(fig_p, freqs, psd, idx_hf,
                        'rgba(0,218,243,0.20)',   COLORS["primary_dim"],       'HF')

        peak_psd = float(np.max(psd)) if len(psd) else 1.0
        for band, label, color in [
            (lf_band, f"LF\n{freq_m.get('LF norm (%)',0):.0f}%", COLORS["tertiary_fixed_dim"]),
            (hf_band, f"HF\n{freq_m.get('HF norm (%)',0):.0f}%", COLORS["primary_dim"]),
        ]:
            fig_p.add_annotation(
                x=(band[0] + band[1]) / 2, y=peak_psd * 0.75,
                text=label, showarrow=False,
                font=dict(color=color, size=10))

        set_layout(fig_p, "Welch's Power Spectral Density", xaxis_title="Frequency (Hz)", yaxis_title="PSD (ms²/Hz)")
        fig_p.update_layout(height=420, xaxis=dict(range=[0, 0.5]))
        st.plotly_chart(fig_p, use_container_width=True)

        # Clinical cards
        lf_hf_interp = interpret_hrv(time_m if 'time_m' in dir() else {}, freq_m)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;margin-top:0.75rem;">
          <div class="clinical-card">
            <div class="clinical-title">🟠 LF Band (Sympathetic)</div>
            <div class="clinical-body">
              {lf_band[0]}–{lf_band[1]} Hz · Power:
              <strong>{freq_m.get('LF Power (ms²)',0):.1f} ms²</strong>
              ({freq_m.get('LF norm (%)',0):.0f}% normalised)
            </div>
          </div>
          <div class="clinical-card">
            <div class="clinical-title">🔵 HF Band (Parasympathetic)</div>
            <div class="clinical-body">
              {hf_band[0]}–{hf_band[1]} Hz · Power:
              <strong>{freq_m.get('HF Power (ms²)',0):.1f} ms²</strong>
              ({freq_m.get('HF norm (%)',0):.0f}% normalised)
            </div>
          </div>
        </div>
        <div class="clinical-card" style="margin-top:0.75rem;">
          <div class="clinical-title">⚖️ Sympathovagal Balance</div>
          <div class="clinical-body">{lf_hf_interp.get("lf_hf_class","—")}</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
