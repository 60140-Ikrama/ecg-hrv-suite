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
    sentinel_header("Pipeline Overview", badge="OEL System")

    # ── Pipeline diagram ────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#1a1c1f;border:1px solid #1e2023;border-radius:0.5rem;
                padding:1.5rem 2rem;margin-bottom:1.5rem;">
      <div style="font-family:'Manrope',sans-serif;font-size:0.6rem;font-weight:800;
                  color:#849396;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">
        Algorithmic HRV Pipeline
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center;">
        <div style="background:rgba(0,218,243,0.12);border:1px solid #00daf3;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#c3f5ff;text-transform:uppercase;letter-spacing:0.06em;">
          📡 ECG Acquisition
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:#1e2023;border:1px solid #282a2d;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#bac9cc;text-transform:uppercase;letter-spacing:0.06em;">
          🧹 Preprocessing
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:#1e2023;border:1px solid #282a2d;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#bac9cc;text-transform:uppercase;letter-spacing:0.06em;">
          ❤️ R-Peak Detection
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:#1e2023;border:1px solid #282a2d;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#bac9cc;text-transform:uppercase;letter-spacing:0.06em;">
          ⏱️ RR Intervals
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:#1e2023;border:1px solid #282a2d;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#bac9cc;text-transform:uppercase;letter-spacing:0.06em;">
          ⚠️ Ectopic Removal
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:rgba(195,244,0,0.08);border:1px solid #c3f400;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#c3f400;text-transform:uppercase;letter-spacing:0.06em;">
          📈 HRV Analysis
        </div>
        <span style="color:#3b494c;font-size:1.2rem;">›</span>
        <div style="background:rgba(255,186,56,0.08);border:1px solid #ffba38;border-radius:0.25rem;
                    padding:0.5rem 0.9rem;font-family:'Manrope',sans-serif;font-size:0.7rem;
                    font-weight:700;color:#ffba38;text-transform:uppercase;letter-spacing:0.06em;">
          📊 Dashboards
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Dashboard cards ─────────────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="medium")

    dashboards = [
        ("1", "📡", "Signal Acquisition", "Upload ECG files (.csv, .mat, .dat, .edf, .txt). Batch multi-file support.", "primary"),
        ("2", "🧹", "Preprocessing", "Bandpass filter, baseline wander removal, and wavelet/notch denoising.", "primary"),
        ("3", "❤️", "R-Peak Detection", "Pan-Tompkins, NeuroKit, Hamilton algorithms with overlay visualization.", "green"),
        ("4", "⏱️", "RR Interval Analysis", "RR tachogram, time-series view, and variability pattern display.", "green"),
        ("5", "⚠️", "Ectopic Correction", "CRITICAL: Detects and interpolates ectopic beats. Before/after comparison.", "amber"),
        ("6", "📈", "Time-Domain HRV", "SDNN, RMSSD, NN50, pNN50, Mean RR — with KPI cards and bar charts.", "primary"),
        ("7", "📊", "Frequency-Domain HRV", "Welch PSD with LF/HF band highlights and sympathovagal interpretation.", "green"),
        ("8", "🔬", "Non-Linear HRV", "Poincaré plot with SD1/SD2 ellipse and entropy metrics.", "amber"),
        ("9", "⚙️", "Settings", "Full pipeline control from the sidebar — updates all dashboards live.", "primary"),
        ("10", "📁", "Multi-File Comparison", "Side-by-side HRV metrics, PSD overlay, statistical comparison table.", "green"),
    ]

    for i, (num, icon, title, desc, accent) in enumerate(dashboards):
        col = col1 if i % 2 == 0 else col2
        accent_color = {"primary": "#00daf3", "green": "#c3f400", "amber": "#ffba38"}[accent]
        col.markdown(f"""
        <div style="background:#1a1c1f;border:1px solid #1e2023;border-radius:0.375rem;
                    padding:1rem 1.25rem;margin-bottom:0.75rem;
                    border-left:3px solid {accent_color};">
          <div style="font-family:'Manrope',sans-serif;font-size:0.6rem;font-weight:800;
                      color:#849396;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.25rem;">
            Dashboard {num}
          </div>
          <div style="font-family:'Manrope',sans-serif;font-size:0.9rem;font-weight:700;
                      color:#e2e2e6;margin-bottom:0.35rem;">{icon} {title}</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.75rem;color:#bac9cc;line-height:1.5;">
            {desc}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Quick Start ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:rgba(0,218,243,0.06);border:1px solid rgba(0,218,243,0.2);
                border-radius:0.5rem;padding:1rem 1.5rem;margin-top:0.5rem;">
      <div style="font-family:'Manrope',sans-serif;font-size:0.65rem;font-weight:800;
                  color:#00daf3;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">
        🚀 Quick Start Guide
      </div>
      <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#bac9cc;line-height:1.8;">
        1. Navigate to <strong style="color:#c3f5ff;">📡 Input & Acquisition</strong> and upload your ECG file(s).<br>
        2. Adjust filter and algorithm settings from the <strong style="color:#c3f5ff;">sidebar</strong> at any time.<br>
        3. Follow the pipeline pages in order — each builds on the previous step's results.<br>
        4. After completing the pipeline, visit <strong style="color:#c3f400;">📁 Multi-File Comparison</strong> and 
           <strong style="color:#ffba38;">📑 Report Generation</strong> for academic output.
      </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
