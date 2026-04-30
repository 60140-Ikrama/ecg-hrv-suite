"""
Clinical Sentinel — ECG & HRV Analysis Suite
Landing page: Pipeline overview and system intro.
"""
import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from components.theme import inject_stitch_theme, sentinel_header, COLORS
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(
    page_title="Clinical Sentinel — ECG & HRV Suite",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    inject_stitch_theme()
    render_sidebar_settings()

    # ── Hero Section ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-section">
      <div class="hero-ecg">
        <svg width="300" height="90" viewBox="0 0 300 90">
          <path d="M0,45 L40,45 L52,40 L64,45 L80,45 L87,18 L91,78 L95,5 L99,52 L110,45
                   L150,45 L162,40 L174,45 L190,45 L197,18 L201,78 L205,5 L209,52 L220,45
                   L260,45 L272,40 L284,45 L300,45"
                stroke="#00daf3" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="hero-eyebrow">&#x1F9E0; Clinical Sentinel &nbsp;&middot;&nbsp; ECG &amp; HRV Suite</div>
      <div class="hero-title">
        <span class="accent">Biomedical Signal</span><br>Analysis Platform
      </div>
      <div class="hero-subtitle">
        Research-grade ECG acquisition, preprocessing, R-peak detection,
        ectopic correction and full HRV analysis. Now featuring <b>Signal Quality-Aware Adaptive Analysis (SQI)</b>.
      </div>
      <div class="hero-pills">
        <div class="hero-pill"><span class="dot cyan"></span> Live Processing</div>
        <div class="hero-pill"><span class="dot green"></span> Adaptive SQI</div>
        <div class="hero-pill"><span class="dot amber"></span> 6 Algorithms</div>
        <div class="hero-pill"><span class="dot" style="background:#ffba38;animation-delay:.9s"></span> Confidence-Aware</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pipeline Timeline ─────────────────────────────────────────────────────
    steps = [
        ("📡", "Acquire",   "active"),
        ("🧹", "Adaptive",  "green"),
        ("❤️", "R-Peaks",  "green"),
        ("⏱️", "RR",       ""),
        ("⚠️", "Ectopic",  "amber"),
        ("📈", "HRV",      "green"),
        ("📊", "PSD",      ""),
        ("🔬", "Nonlinear","amber"),
        ("📁", "Compare",  ""),
        ("🫀", "Risk",     "amber"),
        ("📑", "Report",   "green"),
    ]
    nodes = ""
    for i, (icon, lbl, cls) in enumerate(steps):
        lbl_cls = "active" if cls == "active" else ""
        nodes += (
            f'<div class="pipe-node">'
            f'<div class="pipe-node-circle {cls}">{icon}</div>'
            f'<div class="pipe-node-label {lbl_cls}">{lbl}</div>'
            f'</div>'
        )
        if i < len(steps) - 1:
            nodes += '<div class="pipe-connector"></div>'

    st.markdown(f"""
    <div class="section-header" style="margin-bottom:0.6rem;">Algorithmic Pipeline</div>
    <div class="pipeline-timeline">{nodes}</div>
    """, unsafe_allow_html=True)

    # ── Dashboard Cards ───────────────────────────────────────────────────────
    cards = [
        ("01","📡","Signal Acquisition",
         "Upload ECG files (.csv, .mat, .dat, .edf, .txt). Batch support &amp; URL download.",
         "cyan","Input"),
        ("02","🧹","Adaptive Preprocessing",
         "SQI-aware filtering: Selects denoising strategy based on signal quality index.",
         "cyan","Filter"),
        ("03","❤️","R-Peak Detection",
         "Pan-Tompkins, NeuroKit, Hamilton &amp; Elgendi algorithms with overlay visualization.",
         "green","Detection"),
        ("04","⏱️","RR Interval Analysis",
         "RR tachogram, histogram, time-series view, variability patterns and SQI scoring.",
         "cyan","Intervals"),
        ("05","⚠️","Ectopic Correction",
         "Multi-method ectopic detection with linear/spline interpolation. Before/after view.",
         "amber","Critical"),
        ("06","📈","Time-Domain HRV",
         "SDNN, RMSSD, pNN50 — with confidence scores derived from signal quality.",
         "green","HRV"),
        ("07","📊","Frequency-Domain HRV",
         "Welch PSD with LF/HF band highlights and sympathovagal interpretation.",
         "green","Spectral"),
        ("08","🔬","Non-Linear HRV",
         "Poincaré plot with SD1/SD2 ellipse, Sample Entropy, ApEn and DFA scaling.",
         "amber","Nonlinear"),
        ("09","📁","Multi-File Comparison",
         "Side-by-side HRV metrics, PSD overlay and statistical table across recordings.",
         "cyan","Compare"),
        ("10","🫀","Heart Disease Detection",
         "Rule-based + ML risk assessment with confidence scores and clinical notes.",
         "amber","Clinical"),
        ("11","📑","Report Generation",
         "Export PDF/DOCX/LaTeX with all charts, risk assessment &amp; confidence analytics.",
         "green","Report"),
    ]

    html = '<div class="dash-grid">'
    for idx, (num, icon, title, desc, cls, tag) in enumerate(cards):
        delay = f"animation-delay:{idx * 0.05:.2f}s"
        html += (
            f'<div class="dash-card {cls}" style="{delay}">'
            f'  <div class="dash-card-bar {cls}"></div>'
            f'  <div class="dash-card-num">#{num}</div>'
            f'  <span class="dash-card-icon">{icon}</span>'
            f'  <div class="dash-card-title">{title}</div>'
            f'  <div class="dash-card-desc">{desc}</div>'
            f'  <span class="dash-card-tag {cls}">{tag}</span>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # ── Quick Start ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="qs-section">
      <div class="qs-eyebrow">&#x1F680; Quick Start Guide</div>
      <div class="qs-steps">
        <div class="qs-step">
          <div class="qs-num">1</div>
          <div class="qs-text">Navigate to
            <strong style="color:#c3f5ff;">&#x1F4E1; Input &amp; Acquisition</strong>
            and upload your ECG file — or paste a remote download URL.
          </div>
        </div>
        <div class="qs-step">
          <div class="qs-num">2</div>
          <div class="qs-text">Review signal quality in 
            <strong style="color:#c3f5ff;">🧹 Adaptive Preprocessing</strong>. The system will auto-select the best filter.
          </div>
        </div>
        <div class="qs-step">
          <div class="qs-num">3</div>
          <div class="qs-text">Analyze HRV and Risk metrics — check the <b>Confidence Badge</b> on each card.
          </div>
        </div>
        <div class="qs-step">
          <div class="qs-num">4</div>
          <div class="qs-text">Finish with
            <strong style="color:#ffba38;">&#x1F4C4; Report Generation</strong> to export PDF, Word, or <b>LaTeX</b>.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats Footer ──────────────────────────────────────────────────────────
    n_files = len(st.session_state.get("ecg_files", {}))
    st.markdown(f"""
    <div class="stats-footer">
      <div class="stats-item">Version <span class="val">v2.2.0</span></div>
      <div class="stats-dot"></div>
      <div class="stats-item">Dashboards <span class="val">11</span></div>
      <div class="stats-dot"></div>
      <div class="stats-item">Files Loaded <span class="val">{n_files}</span></div>
      <div class="stats-dot"></div>
      <div class="stats-item">Engine <span class="val">NeuroKit2 · SciPy · Streamlit</span></div>
      <div class="stats-dot"></div>
      <div class="stats-item">Course <span class="val">Biomedical Signal Processing — OEL</span></div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
