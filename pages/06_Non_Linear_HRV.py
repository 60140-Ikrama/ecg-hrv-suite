"""Dashboard 8 — Non-Linear HRV: Poincaré, SampEn, ApEn, DFA"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, kpi_card, section_header,
                               COLORS, get_plot_layout, set_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import (get_nonlinear_hrv, sample_entropy,
                                 approximate_entropy, detrended_fluctuation_analysis)

st.set_page_config(page_title="Non-Linear HRV · Clinical Sentinel",
                   page_icon="🔬", layout="wide")


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active    = st.session_state.get("active_file", "")
    enable_dfa = st.session_state.get("enable_dfa", True)
    sentinel_header("Dashboard 8 · Non-Linear HRV", badge="Poincaré", active_file=active)
    pipeline_status_bar("Nonlinear")

    if not active or active not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("⚠️  Process RR intervals in **⏱️ RR & Ectopics** first.")
        return

    clean_rr = st.session_state["clean_rr_intervals"][active]
    nl_m     = get_nonlinear_hrv(clean_rr)

    if "metrics" not in st.session_state:
        st.session_state["metrics"] = {}
    if active not in st.session_state["metrics"]:
        st.session_state["metrics"][active] = {}
    st.session_state["metrics"][active].update(nl_m)

    sd1   = nl_m.get("SD1 (ms)", 0)
    sd2   = nl_m.get("SD2 (ms)", 0)
    ratio = nl_m.get("SD1/SD2",  0)
    area  = nl_m.get("Ellipse Area (ms²)", 0)

    # ── SampEn & ApEn ─────────────────────────────────────────────────────────
    rr_short = clean_rr[:min(300, len(clean_rr))]
    with st.spinner("Computing entropy metrics…"):
        samp_en = sample_entropy(rr_short)
        apen    = approximate_entropy(rr_short)
    samp_en_str = f"{samp_en:.3f}" if np.isfinite(samp_en) else "N/A"
    apen_str    = f"{apen:.3f}"    if np.isfinite(apen)    else "N/A"
    st.session_state["metrics"][active]["Sample Entropy"] = (
        round(samp_en, 3) if np.isfinite(samp_en) else None)
    st.session_state["metrics"][active]["Approx Entropy"] = (
        round(apen, 3) if np.isfinite(apen) else None)

    # ── DFA ───────────────────────────────────────────────────────────────────
    dfa_result = {}
    if enable_dfa:
        with st.spinner("Computing DFA…"):
            dfa_result = detrended_fluctuation_analysis(clean_rr)
        a1, a2 = dfa_result.get("alpha1", float('nan')), dfa_result.get("alpha2", float('nan'))
        st.session_state["metrics"][active]["DFA α1"] = (round(a1, 3) if np.isfinite(a1) else None)
        st.session_state["metrics"][active]["DFA α2"] = (round(a2, 3) if np.isfinite(a2) else None)
        a1_str = f"{a1:.3f}" if np.isfinite(a1) else "N/A"
        a2_str = f"{a2:.3f}" if np.isfinite(a2) else "N/A"
    else:
        a1_str, a2_str = "Off", "Off"

    # ── KPI row ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.75rem;margin-bottom:1.25rem;">
      {kpi_card("SD1",           f"{sd1:.1f}",   "ms",  accent="primary")}
      {kpi_card("SD2",           f"{sd2:.1f}",   "ms",  accent="green")}
      {kpi_card("SD1 / SD2",     f"{ratio:.3f}",        accent="amber")}
      {kpi_card("Sample Entropy", samp_en_str,           accent="primary")}
      {kpi_card("Approx Entropy", apen_str,              accent="green")}
      {kpi_card("DFA α1",         a1_str,                accent="amber")}
    </div>
    """, unsafe_allow_html=True)

    # ── Layout: Poincaré | Metrics ────────────────────────────────────────────
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        section_header("Poincaré Plot: RR(n) vs RR(n+1)")
        rr_n, rr_n1 = clean_rr[:-1], clean_rr[1:]
        mean_rr = float(np.mean(clean_rr))

        fig = go.Figure()
        # Scatter
        fig.add_trace(go.Scatter(
            x=rr_n, y=rr_n1, mode='markers', name='RR Pairs',
            marker=dict(color=COLORS["primary_dim"], size=5, opacity=0.5,
                        line=dict(color='rgba(255,255,255,0.1)', width=0.5)),
            hovertemplate="RR(n)=%{x:.1f} ms<br>RR(n+1)=%{y:.1f} ms<extra></extra>"))
        # Identity line
        rmin = min(float(np.min(rr_n)), float(np.min(rr_n1)))
        rmax = max(float(np.max(rr_n)), float(np.max(rr_n1)))
        fig.add_trace(go.Scatter(
            x=[rmin, rmax], y=[rmin, rmax], mode='lines',
            name='Identity', line=dict(color=COLORS["outline_variant"],
                                        dash='dash', width=1.5)))
        # SD1/SD2 Ellipse
        theta = np.linspace(0, 2 * np.pi, 300)
        rot   = np.pi / 4
        x_e = mean_rr + sd2 * np.cos(theta) * np.cos(rot) - sd1 * np.sin(theta) * np.sin(rot)
        y_e = mean_rr + sd2 * np.cos(theta) * np.sin(rot) + sd1 * np.sin(theta) * np.cos(rot)
        fig.add_trace(go.Scatter(
            x=x_e, y=y_e, mode='lines', name='SD1/SD2 Ellipse',
            line=dict(color=COLORS["secondary_fixed"], width=2),
            fill='toself', fillcolor='rgba(195,244,0,0.05)'))
        # SD axes
        for dx, dy, name, color in [
            (sd1 * np.cos(rot + np.pi/2), sd1 * np.sin(rot + np.pi/2),
             f'SD1={sd1:.1f}ms', COLORS["primary_dim"]),
            (sd2 * np.cos(rot),           sd2 * np.sin(rot),
             f'SD2={sd2:.1f}ms', COLORS["tertiary_fixed_dim"]),
        ]:
            fig.add_trace(go.Scatter(
                x=[mean_rr - dx, mean_rr + dx],
                y=[mean_rr - dy, mean_rr + dy],
                mode='lines', name=name,
                line=dict(color=color, dash='dot', width=2)))

        set_layout(fig, "Poincaré Plot", xaxis_title="RR(n) (ms)", yaxis_title="RR(n+1) (ms)")
        fig.update_layout(height=460, yaxis_scaleanchor="x")
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    with col2:
        section_header("Non-Linear Metrics")
        items = [
            ("SD1 (ms)",           f"{sd1:.2f}",   "Short-term HRV (≈ RMSSD/√2)"),
            ("SD2 (ms)",           f"{sd2:.2f}",   "Long-term HRV (related to SDNN)"),
            ("SD1/SD2",            f"{ratio:.3f}", "Short- vs long-term balance"),
            ("Ellipse Area (ms²)", f"{area:.1f}",  "Total Poincaré scatter area"),
            ("Sample Entropy",     samp_en_str,    "Signal complexity / irregularity"),
            ("Approx Entropy",     apen_str,       "Regularity estimate (ApEn)"),
        ]
        if enable_dfa:
            items += [
                ("DFA α1", a1_str, "Short-term scaling (4–16 beats)"),
                ("DFA α2", a2_str, "Long-term scaling (16–64 beats)"),
            ]
        html = ""
        for name, val, desc in items:
            html += f"""
            <div style="padding:0.65rem 0;border-bottom:1px solid #1e2023;">
              <div style="font-size:0.6rem;color:#849396;text-transform:uppercase;
                          letter-spacing:0.1em;font-family:'Inter';">{name}</div>
              <div style="font-family:'Manrope';font-size:1.2rem;font-weight:800;
                          color:#c3f5ff;margin:0.1rem 0;">{val}</div>
              <div style="font-size:0.7rem;color:#3b494c;font-family:'Inter';">{desc}</div>
            </div>"""
        st.markdown(f'<div style="background:#1a1c1f;border:1px solid #1e2023;'
                    f'border-radius:0.375rem;padding:0.5rem 1rem;">{html}</div>',
                    unsafe_allow_html=True)

        st.markdown(f"""
        <div class="clinical-card" style="margin-top:1rem;">
          <div class="clinical-title">💡 Poincaré Interpretation</div>
          <div class="clinical-body">
            <strong>SD1</strong> ≈ parasympathetic beat-to-beat variability (RMSSD/√2).<br><br>
            <strong>SD2</strong> ≈ overall long-term variability (related to SDNN).<br><br>
            <strong>SD1/SD2 = {ratio:.3f}</strong>:
            {'High ratio → dominant short-term (parasympathetic) variability.' if ratio > 0.75
             else 'Low ratio → dominant long-term (sympathetic-influenced) variability.'}
          </div>
        </div>""", unsafe_allow_html=True)

    # ── DFA Plot ──────────────────────────────────────────────────────────────
    if enable_dfa and len(dfa_result.get("scales", [])) >= 4:
        section_header("Detrended Fluctuation Analysis (DFA)")
        scales = dfa_result["scales"]
        fluct  = dfa_result["fluct"]
        a1, a2 = dfa_result["alpha1"], dfa_result["alpha2"]

        fig_d = go.Figure()
        fig_d.add_trace(go.Scatter(
            x=np.log10(scales), y=np.log10(fluct),
            mode='markers+lines', name='F(n)',
            marker=dict(color=COLORS["primary_dim"], size=6),
            line=dict(color=COLORS["primary_dim"], width=1.5)))

        # Regression lines
        for s_min, s_max, alpha, color, lbl in [
            (4, 16, a1, COLORS["secondary_fixed"],      f"α1={a1:.3f}" if np.isfinite(a1) else "α1"),
            (16, 64, a2, COLORS["tertiary_fixed_dim"],  f"α2={a2:.3f}" if np.isfinite(a2) else "α2"),
        ]:
            mask = (scales >= s_min) & (scales <= s_max)
            if np.sum(mask) >= 2 and np.isfinite(alpha):
                lx = np.log10(scales[mask])
                ly = np.log10(fluct[mask])
                c  = np.polyfit(lx, ly, 1)
                x_line = np.array([lx.min(), lx.max()])
                fig_d.add_trace(go.Scatter(
                    x=x_line, y=np.polyval(c, x_line),
                    mode='lines', name=lbl,
                    line=dict(color=color, dash='dash', width=2)))

        set_layout(fig_d, "Detrended Fluctuation Analysis", xaxis_title="log₁₀(Scale n)", yaxis_title="log₁₀(F(n))")
        fig_d.update_layout(height=360)
        st.plotly_chart(fig_d, use_container_width=True)

        # DFA interpretation
        interp_a1 = ("N/A" if not np.isfinite(a1) else
                     "White noise (uncorrelated)" if a1 < 0.5 else
                     "Long-range correlations — healthy HRV" if a1 < 1.0 else
                     "1/f noise (pink noise)" if a1 < 1.5 else
                     "Brownian noise (over-correlated)")
        st.markdown(f"""
        <div class="clinical-card" style="margin-top:0.75rem;">
          <div class="clinical-title">📐 DFA Interpretation</div>
          <div class="clinical-body">
            <strong>α1 = {a1_str}</strong> (short-term, 4–16 beats): {interp_a1}<br><br>
            <strong>α2 = {a2_str}</strong> (long-term, 16–64 beats): overall fractal scaling.
            Healthy resting α1 is typically 0.9–1.2.
          </div>
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
