"""Dashboard 09 — Heart Disease Detection & Cardiovascular Risk Assessment"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header,
                               kpi_card, COLORS, set_layout)
from components.sidebar_settings import render_sidebar_settings
from utils.heart_disease_detection import classify_cardiovascular_risk

st.set_page_config(
    page_title="Heart Disease Detection · Clinical Sentinel",
    page_icon="🫀", layout="wide"
)

# ── Risk level styling ─────────────────────────────────────────────────────────
RISK_STYLES = {
    "Normal":    {"color": "#4caf7d", "bg": "#0d2a1a", "border": "#4caf7d", "icon": "✅"},
    "Mild Risk": {"color": "#ffba38", "bg": "#2a1e00", "border": "#ffba38", "icon": "⚠️"},
    "High Risk": {"color": "#f44336", "bg": "#2a0a0a", "border": "#f44336", "icon": "🚨"},
}

STATUS_COLORS = {
    "normal":      COLORS["secondary_fixed"],
    "mild_risk":   "#ffba38",
    "high_risk":   COLORS["error"],
    "unavailable": COLORS["on_surface_variant"],
}


def _gauge_chart(score: float, risk_level: str) -> go.Figure:
    """Build a semicircular risk gauge."""
    style = RISK_STYLES.get(risk_level, RISK_STYLES["Normal"])

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "/100", "font": {"size": 32, "color": style["color"]}},
        title={"text": f"{style['icon']} {risk_level}", "font": {"size": 20, "color": style["color"]}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": COLORS["outline"],
                "tickfont": {"color": COLORS["on_surface_variant"], "size": 10},
            },
            "bar":  {"color": style["color"], "thickness": 0.25},
            "bgcolor": COLORS["surface_container_lowest"],
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30],  "color": "rgba(76,175,125,0.15)"},
                {"range": [30, 60],  "color": "rgba(255,186,56,0.15)"},
                {"range": [60, 100], "color": "rgba(244,67,54,0.15)"},
            ],
            "threshold": {
                "line": {"color": style["color"], "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        }
    ))

    layout = {
        "paper_bgcolor": COLORS["surface_container_lowest"],
        "plot_bgcolor":  COLORS["surface_container_lowest"],
        "font":  {"family": "Manrope, Inter, sans-serif", "color": COLORS["on_surface"]},
        "margin": dict(l=30, r=30, t=40, b=10),
        "height": 300,
    }
    fig.update_layout(**layout)
    return fig


def _probability_bar(ml_result: dict) -> go.Figure:
    """Horizontal bar chart showing ML class probabilities."""
    probs = ml_result.get("probabilities", {})
    labels = ["Normal", "Mild Risk", "High Risk"]
    values = [probs.get(k, 0.0) for k in labels]
    colors = ["#4caf7d", "#ffba38", "#f44336"]

    fig = go.Figure(go.Bar(
        y=labels, x=values,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
        textfont=dict(color=COLORS["on_surface_variant"], size=11),
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["surface_container_lowest"],
        plot_bgcolor=COLORS["surface_container_lowest"],
        font={"family": "Manrope, Inter, sans-serif", "color": COLORS["on_surface"]},
        xaxis=dict(range=[0, 110], showgrid=False, zeroline=False,
                   tickfont=dict(color=COLORS["on_surface_variant"])),
        yaxis=dict(showgrid=False,
                   tickfont=dict(color=COLORS["on_surface_variant"], size=12)),
        margin=dict(l=10, r=30, t=10, b=10),
        height=160,
        showlegend=False,
    )
    return fig


def _flags_table_html(flags: dict) -> str:
    """Render the metric flags as styled HTML cards."""
    rows = ""
    for metric, info in flags.items():
        status  = info.get("status", "unavailable")
        color   = STATUS_COLORS.get(status, COLORS["on_surface_variant"])
        icon    = {"normal": "✅", "mild_risk": "⚠️", "high_risk": "🚨",
                   "unavailable": "—"}.get(status, "—")
        value   = info.get("value", "N/A")
        note    = info.get("clinical_note", "")
        thr     = info.get("threshold", "")
        rows += f"""
        <div style="border-left:3px solid {color};padding:0.6rem 0.8rem;
                    margin-bottom:0.5rem;background:{COLORS['surface_container']};
                    border-radius:0 0.3rem 0.3rem 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.2rem;">
            <span style="font-weight:700;color:{COLORS['on_surface']};font-size:0.85rem;">{icon} {metric}</span>
            <span style="background:{color}22;color:{color};font-size:0.75rem;font-weight:700;
                         padding:0.1rem 0.5rem;border-radius:1rem;border:1px solid {color}55;">{value}</span>
          </div>
          <div style="font-size:0.75rem;color:{COLORS['on_surface_variant']};margin-bottom:0.15rem;">{note}</div>
          <div style="font-size:0.68rem;color:{COLORS['outline']};font-family:monospace;">Threshold: {thr}</div>
        </div>
        """
    return f'<div style="margin-top:0.5rem;">{rows}</div>'


def _risk_card(fname: str, result: dict) -> str:
    """Compact risk card HTML for multi-file view."""
    risk   = result["risk_level"]
    style  = RISK_STYLES.get(risk, RISK_STYLES["Normal"])
    conf   = result.get("confidence", 0)
    score  = result.get("score", 0)
    method = result.get("method", "—")
    return f"""
    <div style="border:1px solid {style['border']};border-left:4px solid {style['border']};
                background:{style['bg']};border-radius:0.4rem;padding:0.85rem 1rem;
                margin-bottom:0.6rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
        <span style="font-weight:800;font-size:0.85rem;color:#849396;">{fname}</span>
        <span style="color:{style['color']};font-weight:800;font-size:0.9rem;">{style['icon']} {risk}</span>
      </div>
      <div style="font-size:0.75rem;color:{COLORS['on_surface_variant']};">
        Risk Score: <strong style="color:{style['color']};">{score:.0f}/100</strong> &nbsp;|&nbsp;
        Confidence: <strong>{conf:.0f}%</strong> &nbsp;|&nbsp;
        Method: {method}
      </div>
    </div>
    """


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 09 · Heart Disease Detection", badge="Clinical")
    pipeline_status_bar("HRV")

    # ── Custom CSS for this dashboard ──────────────────────────────────────────
    st.markdown("""
    <style>
    .risk-explain {
        background: var(--surface-container, #1a1c1f);
        border-radius: 0.5rem;
        padding: 1rem 1.2rem;
        font-size: 0.82rem;
        line-height: 1.6;
        color: #bac9cc;
        border: 1px solid #1e2023;
    }
    </style>
    """, unsafe_allow_html=True)

    metrics_dict  = st.session_state.get("metrics",       {})
    sqi_cache     = st.session_state.get("sqi_cache",     {})
    raw_rr_cache  = st.session_state.get("raw_rr_intervals", {})

    if not metrics_dict:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#849396;">
          <div style="font-size:3.5rem;">🫀</div>
          <div style="font-family:'Manrope';font-size:1rem;font-weight:700;
                      color:#bac9cc;margin-top:0.5rem;">No HRV Analysis Data Found</div>
          <div style="font-size:0.8rem;margin-top:0.25rem;">
            Complete the pipeline through <strong>Dashboard 06 · HRV Analysis</strong> to enable risk classification.
          </div>
        </div>""", unsafe_allow_html=True)
        return

    files = list(metrics_dict.keys())
    active = st.session_state.get("active_file", files[0] if files else "")

    # ── File selector ──────────────────────────────────────────────────────────
    if len(files) > 1:
        active = st.selectbox("Select file for detailed view", files,
                              index=files.index(active) if active in files else 0,
                              key="hdd_file_select")

    metrics = metrics_dict.get(active, {})
    raw_rr  = raw_rr_cache.get(active)
    pct_ectopic = 0.0
    if raw_rr is not None and len(raw_rr) > 0:
        clean_rr = st.session_state.get("clean_rr_intervals", {}).get(active, raw_rr)
        # Approximate ectopic rate from difference in variability
        from utils.hrv_analysis import detect_ectopic_beats
        mask = detect_ectopic_beats(raw_rr)
        pct_ectopic = float(np.sum(mask)) / len(raw_rr) * 100

    # ── Run classifier ─────────────────────────────────────────────────────────
    with st.spinner("Running cardiovascular risk analysis…"):
        result = classify_cardiovascular_risk(metrics, pct_ectopic=pct_ectopic, use_ml=True)

    risk_level = result["risk_level"]
    style      = RISK_STYLES.get(risk_level, RISK_STYLES["Normal"])

    # ── Hero risk banner ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{style['bg']};border:1.5px solid {style['border']};
                border-radius:0.6rem;padding:1.25rem 1.5rem;margin-bottom:1.25rem;
                display:flex;align-items:center;gap:1.5rem;">
      <div style="font-size:3rem;line-height:1;">{style['icon']}</div>
      <div>
        <div style="font-size:1.5rem;font-weight:900;color:{style['color']};
                    font-family:'Manrope',sans-serif;">{risk_level}</div>
        <div style="font-size:0.8rem;color:{COLORS['on_surface_variant']};margin-top:0.15rem;">
          Risk Score: <strong style="color:{style['color']};">{result['score']:.0f} / 100</strong>
          &nbsp;·&nbsp; Confidence: <strong>{result['confidence']:.0f}%</strong>
          &nbsp;·&nbsp; Method: {result['method']}
        </div>
        <div style="font-size:0.75rem;color:{COLORS['outline']};margin-top:0.25rem;">File: {active}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Gauge + ML probability ─────────────────────────────────────────────────
    col_gauge, col_proba = st.columns([3, 2])

    with col_gauge:
        section_header("Risk Score Gauge")
        st.plotly_chart(_gauge_chart(result["score"], risk_level),
                        use_container_width=True)

    with col_proba:
        section_header("Classification Confidence")
        ml_res = result.get("ml_result")
        if ml_res and "probabilities" in ml_res:
            st.plotly_chart(_probability_bar(ml_res), use_container_width=True)
            st.markdown(f"""
            <div style="font-size:0.72rem;color:{COLORS['on_surface_variant']};
                        margin-top:-0.5rem;text-align:center;">
              ML Model: Random Forest · Trained on synthetic HRV reference ranges
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-size:0.8rem;color:{COLORS['on_surface_variant']};
                        margin-top:1rem;padding:0.75rem;
                        background:{COLORS['surface_container']};border-radius:0.4rem;">
              ML classifier requires <code>scikit-learn</code>.<br>
              Currently using rule-based classification only.<br>
              Install: <code>pip install scikit-learn</code>
            </div>""", unsafe_allow_html=True)

    # ── Metric flags table ──────────────────────────────────────────────────────
    st.markdown("---")
    section_header("Metric-by-Metric Analysis")
    flags_html = _flags_table_html(result.get("flags", {}))
    st.markdown(flags_html, unsafe_allow_html=True)

    # ── Clinical explanation ────────────────────────────────────────────────────
    st.markdown("---")
    section_header("Clinical Explanation & Recommendation")
    st.markdown(f"""
    <div class="risk-explain">{result.get('explanation','').replace(chr(10), '<br>')}</div>
    """, unsafe_allow_html=True)

    # ── Reference thresholds ────────────────────────────────────────────────────
    st.markdown("---")
    section_header("Clinical Reference Thresholds")
    import pandas as pd
    ref_rows = [
        {"Metric": "SDNN (ms)",     "Normal": "≥ 50",        "Mild Risk": "20–50",    "High Risk": "< 20"},
        {"Metric": "RMSSD (ms)",    "Normal": "≥ 20",        "Mild Risk": "12–20",    "High Risk": "< 12"},
        {"Metric": "Mean HR (bpm)", "Normal": "50–110",      "Mild Risk": "48–130",   "High Risk": "< 48 or > 130"},
        {"Metric": "LF/HF Ratio",  "Normal": "0.7–3.5",     "Mild Risk": "0.5–5.0",  "High Risk": "< 0.5 or > 5.0"},
        {"Metric": "DFA α1",        "Normal": "0.75–1.30",   "Mild Risk": "0.65–1.45","High Risk": "< 0.65 or > 1.45"},
        {"Metric": "Ectopic Rate",  "Normal": "< 5%",        "Mild Risk": "5–15%",    "High Risk": "> 15%"},
    ]
    st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, hide_index=True)

    # ── Multi-file comparison ───────────────────────────────────────────────────
    if len(files) > 1:
        st.markdown("---")
        section_header(f"Multi-File Risk Summary ({len(files)} files)")
        all_html = ""
        for f in files:
            m = metrics_dict.get(f, {})
            rr_f = raw_rr_cache.get(f)
            pct_e = 0.0
            if rr_f is not None and len(rr_f) > 0:
                from utils.hrv_analysis import detect_ectopic_beats as _deb
                msk_f = _deb(rr_f)
                pct_e = float(np.sum(msk_f)) / len(rr_f) * 100
            r_f = classify_cardiovascular_risk(m, pct_ectopic=pct_e, use_ml=True)
            all_html += _risk_card(f, r_f)
        st.markdown(all_html, unsafe_allow_html=True)

        # Comparative score bar chart
        scores = []
        risk_colors = []
        for f in files:
            m = metrics_dict.get(f, {})
            rr_f = raw_rr_cache.get(f)
            pct_e = 0.0
            if rr_f is not None and len(rr_f) > 0:
                from utils.hrv_analysis import detect_ectopic_beats as _deb2
                msk_f = _deb2(rr_f)
                pct_e = float(np.sum(msk_f)) / len(rr_f) * 100
            r_f = classify_cardiovascular_risk(m, pct_ectopic=pct_e, use_ml=False)
            scores.append(r_f["score"])
            risk_colors.append(RISK_STYLES.get(r_f["risk_level"], RISK_STYLES["Normal"])["color"])

        labels = [os.path.splitext(f)[0][:16] for f in files]
        fig_comp = go.Figure(go.Bar(
            x=labels, y=scores,
            marker_color=risk_colors,
            text=[f"{s:.0f}" for s in scores],
            textposition="outside",
            textfont=dict(color=COLORS["on_surface_variant"], size=11),
        ))
        set_layout(fig_comp, "Risk Score Comparison", xaxis_title="File", yaxis_title="Risk Score (0–100)")
        fig_comp.update_layout(height=300, showlegend=False, yaxis=dict(range=[0, 115]))
        st.plotly_chart(fig_comp, use_container_width=True)

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:2rem;padding:0.75rem 1rem;border-radius:0.4rem;
                background:{COLORS['surface_container']};border:1px solid {COLORS['outline_variant']};
                font-size:0.72rem;color:{COLORS['on_surface_variant']};text-align:center;">
      ⚕️ <strong>Medical Disclaimer:</strong> This analysis is based on automated HRV pattern recognition
      and is intended for research and educational purposes only. It does not constitute medical advice.
      Always consult a qualified cardiologist for clinical decisions.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
