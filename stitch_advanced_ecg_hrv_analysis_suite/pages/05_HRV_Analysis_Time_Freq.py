"""Dashboards 6 & 7 — Time-Domain and Frequency-Domain HRV"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, kpi_card, section_header, clinical_interpretation, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import get_time_domain_hrv, get_freq_domain_hrv, interpret_hrv

st.set_page_config(page_title="HRV Analysis · Clinical Sentinel", page_icon="📈", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboards 6 & 7 · HRV Analysis", badge="HRV", active_file=active)
    pipeline_status_bar("HRV")

    if not active or active not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("⚠️  Process RR intervals in **⏱️ RR & Ectopics** first.")
        return

    clean_rr = st.session_state["clean_rr_intervals"][active]

    tab1, tab2 = st.tabs(["📈 Dashboard 6 · Time Domain", "📊 Dashboard 7 · Frequency Domain"])

    # ───────────────────────────────────────────────────────────────────────
    with tab1:
        time_m = get_time_domain_hrv(clean_rr)

        # Store metrics
        if "metrics" not in st.session_state:
            st.session_state["metrics"] = {}
        if active not in st.session_state["metrics"]:
            st.session_state["metrics"][active] = {}
        st.session_state["metrics"][active].update(time_m)

        # KPI row
        sdnn_pct = min(int(time_m.get("SDNN (ms)", 0)), 150)
        rmssd_pct = min(int(time_m.get("RMSSD (ms)", 0)), 100)
        pnn50_pct = min(int(time_m.get("pNN50 (%)", 0)), 100)

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1rem;">
          {kpi_card("Mean RR", f"{time_m.get('Mean RR (ms)',0):.0f}", "ms", accent="primary", bar_pct=60)}
          {kpi_card("Mean HR", f"{time_m.get('Mean HR (bpm)',0):.0f}", "bpm", accent="primary")}
          {kpi_card("SDNN", f"{time_m.get('SDNN (ms)',0):.1f}", "ms", accent="green", bar_pct=sdnn_pct)}
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1.25rem;">
          {kpi_card("RMSSD", f"{time_m.get('RMSSD (ms)',0):.1f}", "ms", accent="primary", bar_pct=rmssd_pct)}
          {kpi_card("NN50", str(time_m.get('NN50',0)), "beats", accent="amber")}
          {kpi_card("pNN50", f"{time_m.get('pNN50 (%)',0):.1f}", "%", accent="green", bar_pct=pnn50_pct)}
        </div>
        """, unsafe_allow_html=True)

        # Successive differences bar chart
        section_header("Successive RR Differences (|ΔRR|)")
        diff_rr = np.abs(np.diff(clean_rr))
        beats = np.arange(len(diff_rr))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=beats, y=diff_rr,
            name='|ΔRR|',
            marker_color=COLORS["primary_dim"],
            marker_line=dict(color=COLORS["outline_variant"], width=0.3),
            hovertemplate="Beat %{x}<br>|ΔRR|=%{y:.1f} ms<extra></extra>"
        ))
        fig.add_hline(y=50, line_dash="dot", line_color=COLORS["secondary_fixed"],
                      annotation_text="NN50 threshold (50ms)",
                      annotation_font=dict(color=COLORS["secondary_fixed"], size=10))
        lay = {**PLOTLY_LAYOUT, "height": 300}
        lay["xaxis"]["title"] = "Beat Number"
        lay["yaxis"]["title"] = "|ΔRR| (ms)"
        lay["title"] = None
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        # Clinical
        freq_m = st.session_state["metrics"].get(active, {})
        interp = interpret_hrv(time_m, freq_m)
        st.markdown(f"""
        <div class="clinical-card" style="margin-top:0.75rem;">
          <div class="clinical-title">💡 Time-Domain Clinical Assessment</div>
          <div class="clinical-body">
            <strong>SDNN:</strong> {interp.get('sdnn_class','—')}<br>
            <strong>Vagal Tone (RMSSD):</strong> {interp.get('autonomic','—')}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ───────────────────────────────────────────────────────────────────────
    with tab2:
        lf_band = (st.session_state.get("lf_min", 0.04), st.session_state.get("lf_max", 0.15))
        hf_band = (st.session_state.get("hf_min", 0.15), st.session_state.get("hf_max", 0.40))
        vlf_band = (0.003, lf_band[0])

        freq_m, freqs, psd = get_freq_domain_hrv(
            clean_rr, vlf_band=vlf_band, lf_band=lf_band, hf_band=hf_band)

        if freq_m is None:
            st.warning("Not enough RR data for frequency analysis (need >10 beats with sufficient duration).")
            return

        st.session_state["metrics"][active].update(freq_m)
        # Also save raw PSD for multi-file comparison
        if "psd_data" not in st.session_state:
            st.session_state["psd_data"] = {}
        st.session_state["psd_data"][active] = (freqs, psd)

        # KPI row
        lf_hf = freq_m.get("LF/HF Ratio", 0)
        lf_hf_str = f"{lf_hf:.2f}" if lf_hf == lf_hf else "N/A"
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1.25rem;">
          {kpi_card("LF Power", f"{freq_m.get('LF Power (ms²)',0):.1f}", "ms²", accent="amber")}
          {kpi_card("HF Power", f"{freq_m.get('HF Power (ms²)',0):.1f}", "ms²", accent="primary")}
          {kpi_card("LF/HF Ratio", lf_hf_str, accent="amber" if lf_hf>2 else "green")}
          {kpi_card("Total Power", f"{freq_m.get('Total Power (ms²)',0):.0f}", "ms²", accent="primary")}
        </div>
        """, unsafe_allow_html=True)

        # PSD plot
        section_header("Power Spectral Density (Welch's Method)")
        idx_vlf = np.logical_and(freqs >= vlf_band[0], freqs < vlf_band[1])
        idx_lf = np.logical_and(freqs >= lf_band[0], freqs < lf_band[1])
        idx_hf = np.logical_and(freqs >= hf_band[0], freqs < hf_band[1])

        fig_psd = go.Figure()
        # Full PSD line
        fig_psd.add_trace(go.Scatter(
            x=freqs, y=psd, mode='lines', name='PSD',
            line=dict(color=COLORS["on_surface_variant"], width=1.5)))

        # Band fills
        fig_psd.add_trace(go.Scatter(
            x=np.concatenate([[freqs[idx_vlf][0]], freqs[idx_vlf], [freqs[idx_vlf][-1]]]),
            y=np.concatenate([[0], psd[idx_vlf], [0]]),
            fill='toself', fillcolor='rgba(132,147,150,0.15)',
            line=dict(width=0), name='VLF'))
        fig_psd.add_trace(go.Scatter(
            x=np.concatenate([[freqs[idx_lf][0]], freqs[idx_lf], [freqs[idx_lf][-1]]]),
            y=np.concatenate([[0], psd[idx_lf], [0]]),
            fill='toself', fillcolor='rgba(255,186,56,0.25)',
            line=dict(color=COLORS["tertiary_fixed_dim"], width=1.5), name='LF'))
        fig_psd.add_trace(go.Scatter(
            x=np.concatenate([[freqs[idx_hf][0]], freqs[idx_hf], [freqs[idx_hf][-1]]]),
            y=np.concatenate([[0], psd[idx_hf], [0]]),
            fill='toself', fillcolor='rgba(0,218,243,0.2)',
            line=dict(color=COLORS["primary_dim"], width=1.5), name='HF'))

        # LF/HF annotation
        fig_psd.add_annotation(
            x=(lf_band[0]+lf_band[1])/2, y=max(psd)*0.75,
            text=f"LF<br>{freq_m.get('LF norm (%)',0):.0f}%",
            showarrow=False, font=dict(color=COLORS["tertiary_fixed_dim"], size=10))
        fig_psd.add_annotation(
            x=(hf_band[0]+hf_band[1])/2, y=max(psd)*0.75,
            text=f"HF<br>{freq_m.get('HF norm (%)',0):.0f}%",
            showarrow=False, font=dict(color=COLORS["primary_dim"], size=10))

        lay_psd = {**PLOTLY_LAYOUT, "height": 420}
        lay_psd["xaxis"]["title"] = "Frequency (Hz)"
        lay_psd["xaxis"]["range"] = [0, 0.5]
        lay_psd["yaxis"]["title"] = "PSD (ms²/Hz)"
        lay_psd["title"] = None
        fig_psd.update_layout(**lay_psd)
        st.plotly_chart(fig_psd, use_container_width=True)

        # Interpretation
        lf_hf_interp = interpret_hrv(time_m if time_m else {}, freq_m)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:0.75rem;">
          <div class="clinical-card">
            <div class="clinical-title">🟠 LF Band (Sympathetic Activity)</div>
            <div class="clinical-body">
              The Low-Frequency band ({lf_band[0]}–{lf_band[1]} Hz) reflects 
              <strong>Sympathetic</strong> and mixed autonomic modulation. 
              Power: <strong>{freq_m.get('LF Power (ms²)',0):.1f} ms²</strong> 
              ({freq_m.get('LF norm (%)',0):.0f}% normalized).
            </div>
          </div>
          <div class="clinical-card">
            <div class="clinical-title">🔵 HF Band (Parasympathetic Activity)</div>
            <div class="clinical-body">
              The High-Frequency band ({hf_band[0]}–{hf_band[1]} Hz) reflects 
              <strong>Parasympathetic</strong> (vagal) modulation via RSA. 
              Power: <strong>{freq_m.get('HF Power (ms²)',0):.1f} ms²</strong> 
              ({freq_m.get('HF norm (%)',0):.0f}% normalized).
            </div>
          </div>
        </div>
        <div class="clinical-card" style="margin-top:0.75rem;">
          <div class="clinical-title">⚖️ Sympathovagal Balance</div>
          <div class="clinical-body">{lf_hf_interp.get('lf_hf_class','—')}</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
