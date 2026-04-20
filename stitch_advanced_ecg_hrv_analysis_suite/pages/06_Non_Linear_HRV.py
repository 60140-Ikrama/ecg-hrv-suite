"""Dashboard 8 — Non-Linear HRV: Poincaré Plot, SD1/SD2, Entropy"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, kpi_card, section_header, COLORS, PLOTLY_LAYOUT
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import get_nonlinear_hrv

st.set_page_config(page_title="Non-Linear HRV · Clinical Sentinel", page_icon="🔬", layout="wide")


def sample_entropy(rr_ms: np.ndarray, m: int = 2, r_factor: float = 0.2) -> float:
    """Approximate Sample Entropy computation."""
    if len(rr_ms) < 2 * m:
        return float('nan')
    N = len(rr_ms)
    r = r_factor * np.std(rr_ms, ddof=1)
    
    def count_templates(template_len):
        count = 0
        for i in range(N - template_len):
            for j in range(i + 1, N - template_len):
                if np.max(np.abs(rr_ms[i:i+template_len] - rr_ms[j:j+template_len])) < r:
                    count += 1
        return count

    B = count_templates(m)
    A = count_templates(m + 1)
    if B == 0:
        return float('nan')
    return -np.log(A / B) if A > 0 else float('inf')


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    active = st.session_state.get("active_file", "")
    sentinel_header("Dashboard 8 · Non-Linear HRV", badge="Poincaré", active_file=active)
    pipeline_status_bar("Nonlinear")

    if not active or active not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("⚠️  Process RR intervals in **⏱️ RR & Ectopics** first.")
        return

    clean_rr = st.session_state["clean_rr_intervals"][active]
    nl_m = get_nonlinear_hrv(clean_rr)

    # Store metrics
    if "metrics" not in st.session_state:
        st.session_state["metrics"] = {}
    if active not in st.session_state["metrics"]:
        st.session_state["metrics"][active] = {}
    st.session_state["metrics"][active].update(nl_m)

    # Compute SampEn (limit length for speed)
    with st.spinner("Computing Sample Entropy…"):
        rr_for_entropy = clean_rr[:min(200, len(clean_rr))]
        samp_en = sample_entropy(rr_for_entropy)
        samp_en_str = f"{samp_en:.3f}" if samp_en == samp_en else "N/A"
        st.session_state["metrics"][active]["Sample Entropy"] = round(samp_en, 3) if samp_en == samp_en else None

    # ── KPI row ───────────────────────────────────────────────────────────
    sd1 = nl_m.get("SD1 (ms)", 0)
    sd2 = nl_m.get("SD2 (ms)", 0)
    ratio = nl_m.get("SD1/SD2", 0)
    area = nl_m.get("Ellipse Area (ms²)", 0)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1.25rem;">
      {kpi_card("SD1 (Short-Term)", f"{sd1:.1f}", "ms", accent="primary")}
      {kpi_card("SD2 (Long-Term)", f"{sd2:.1f}", "ms", accent="green")}
      {kpi_card("SD1 / SD2", f"{ratio:.3f}", accent="amber")}
      {kpi_card("Sample Entropy", samp_en_str, accent="primary")}
    </div>
    """, unsafe_allow_html=True)

    # ── Main Layout: Poincaré + metrics ──────────────────────────────────
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        section_header("Poincaré Plot: RR(n) vs RR(n+1)")
        rr_n = clean_rr[:-1]
        rr_n1 = clean_rr[1:]
        mean_rr = np.mean(clean_rr)

        fig = go.Figure()

        # Background density approximation via scatter with low opacity
        fig.add_trace(go.Scatter(
            x=rr_n, y=rr_n1, mode='markers',
            name='RR Pairs',
            marker=dict(
                color=COLORS["primary_dim"],
                size=5, opacity=0.5,
                line=dict(color='rgba(255,255,255,0.1)', width=0.5)
            ),
            hovertemplate="RR(n)=%{x:.1f} ms<br>RR(n+1)=%{y:.1f} ms<extra></extra>"
        ))

        # Line of identity
        r_min = min(np.min(rr_n), np.min(rr_n1))
        r_max = max(np.max(rr_n), np.max(rr_n1))
        fig.add_trace(go.Scatter(
            x=[r_min, r_max], y=[r_min, r_max],
            mode='lines', name='Identity Line',
            line=dict(color=COLORS["outline_variant"], dash='dash', width=1.5)
        ))

        # SD1 / SD2 Ellipse
        theta = np.linspace(0, 2 * np.pi, 300)
        rot = np.pi / 4
        x_ell = mean_rr + sd2 * np.cos(theta) * np.cos(rot) - sd1 * np.sin(theta) * np.sin(rot)
        y_ell = mean_rr + sd2 * np.cos(theta) * np.sin(rot) + sd1 * np.sin(theta) * np.cos(rot)
        fig.add_trace(go.Scatter(
            x=x_ell, y=y_ell, mode='lines', name='SD1/SD2 Ellipse',
            line=dict(color=COLORS["secondary_fixed"], width=2),
            fill='toself', fillcolor='rgba(195,244,0,0.05)'
        ))

        # SD1 axis (perpendicular to identity, length=SD1)
        sd1_dx = sd1 * np.cos(rot + np.pi/2)
        sd1_dy = sd1 * np.sin(rot + np.pi/2)
        fig.add_trace(go.Scatter(
            x=[mean_rr - sd1_dx, mean_rr + sd1_dx],
            y=[mean_rr - sd1_dy, mean_rr + sd1_dy],
            mode='lines', name=f'SD1={sd1:.1f}ms',
            line=dict(color=COLORS["primary_dim"], dash='dot', width=2)
        ))

        # SD2 axis (along identity)
        sd2_dx = sd2 * np.cos(rot)
        sd2_dy = sd2 * np.sin(rot)
        fig.add_trace(go.Scatter(
            x=[mean_rr - sd2_dx, mean_rr + sd2_dx],
            y=[mean_rr - sd2_dy, mean_rr + sd2_dy],
            mode='lines', name=f'SD2={sd2:.1f}ms',
            line=dict(color=COLORS["tertiary_fixed_dim"], dash='dot', width=2)
        ))

        lay = {**PLOTLY_LAYOUT, "height": 480}
        lay["xaxis"]["title"] = "RR(n) (ms)"
        lay["yaxis"]["title"] = "RR(n+1) (ms)"
        lay["yaxis"]["scaleanchor"] = "x"
        lay["title"] = None
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    with col2:
        section_header("Non-Linear Metrics")
        metrics_html = ""
        items = [
            ("SD1 (ms)", f"{sd1:.2f}", "Short-term HRV (parasympathetic)"),
            ("SD2 (ms)", f"{sd2:.2f}", "Long-term HRV (overall variability)"),
            ("SD1/SD2", f"{ratio:.3f}", "Balance of short vs long-term"),
            ("Ellipse Area (ms²)", f"{area:.1f}", "Total Poincaré plot area"),
            ("Sample Entropy", samp_en_str, "Signal complexity/irregularity"),
        ]
        for name, val, desc in items:
            metrics_html += f"""
            <div style="padding:0.75rem 0;border-bottom:1px solid #1e2023;">
              <div style="font-size:0.6rem;color:#849396;text-transform:uppercase;
                          letter-spacing:0.1em;font-family:'Inter';">{name}</div>
              <div style="font-family:'Manrope';font-size:1.3rem;font-weight:800;
                          color:#c3f5ff;margin:0.1rem 0;">{val}</div>
              <div style="font-size:0.7rem;color:#3b494c;font-family:'Inter';">{desc}</div>
            </div>"""
        st.markdown(f'<div style="background:#1a1c1f;border:1px solid #1e2023;border-radius:0.375rem;padding:0.5rem 1rem;">{metrics_html}</div>', unsafe_allow_html=True)

        # Physiology note
        st.markdown(f"""
        <div class="clinical-card" style="margin-top:1rem;">
          <div class="clinical-title">💡 Poincaré Interpretation</div>
          <div class="clinical-body">
            <strong>SD1</strong> reflects beat-to-beat (parasympathetic) variability 
            — equivalent to RMSSD/√2.<br><br>
            <strong>SD2</strong> reflects overall long-term variability 
            — related to SDNN.<br><br>
            <strong>SD1/SD2 = {ratio:.3f}</strong>: 
            {'High ratio → more short-term variability (parasympathetic dominant).' if ratio>0.75 
             else 'Low ratio → more long-term variability (sympathetic-influenced).'}
          </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
