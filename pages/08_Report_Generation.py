"""Dashboard (CLO3) — Professional Report Generation"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, pipeline_status_bar, section_header, COLORS
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import interpret_hrv

st.set_page_config(page_title="Report Generation · Clinical Sentinel", page_icon="📑", layout="wide")


def _interp_row(m: dict) -> str:
    """Quick clinical verdict for a file's metrics."""
    sdnn = m.get("SDNN (ms)", 0)
    lf_hf = m.get("LF/HF Ratio", float('nan'))
    interp = interpret_hrv(m, m)
    return interp.get("lf_hf_class", "N/A")


def build_markdown_report(metrics_dict, settings) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("# Clinical Sentinel — ECG & HRV Analysis Report")
    lines.append(f"\n**Generated:** {ts}")
    lines.append("\n---\n")

    lines.append("## 1. Methodology\n")
    lines.append("### Signal Acquisition")
    lines.append(f"- Files analyzed: {', '.join(metrics_dict.keys())}")
    lines.append(f"- Sampling frequency: **{settings.get('sfreq', 250):.0f} Hz**\n")
    lines.append("### Preprocessing")
    lines.append(f"- Bandpass filter: **{settings.get('lowcut', 0.5):.2f} – {settings.get('highcut', 40):.0f} Hz**")
    lines.append(f"- Baseline wander removal: **{'Yes' if settings.get('remove_baseline', True) else 'No'}**")
    lines.append(f"- Additional noise filter: **{settings.get('noise_method', 'None')}**\n")
    lines.append("### R-Peak Detection")
    lines.append(f"- Algorithm: **{settings.get('rpeak_method', 'NeuroKit')}**\n")
    lines.append("### Ectopic Beat Correction")
    lines.append(f"- Enabled: **{'Yes' if settings.get('remove_ectopic', True) else 'No'}**")
    lines.append(f"- Detection threshold: **{settings.get('ectopic_threshold', 20)}%**")
    lines.append(f"- Interpolation method: **{settings.get('ectopic_interp', 'Linear')}**\n")
    lines.append("### HRV Analysis")
    lines.append(f"- LF band: **{settings.get('lf_min', 0.04):.2f} – {settings.get('lf_max', 0.15):.2f} Hz**")
    lines.append(f"- HF band: **{settings.get('hf_min', 0.15):.2f} – {settings.get('hf_max', 0.40):.2f} Hz**")
    lines.append(f"- PSD method: **Welch's method** (resampled at 4 Hz, Hanning window)\n")

    lines.append("---\n")
    lines.append("## 2. Results\n")

    for fname, m in metrics_dict.items():
        lines.append(f"### File: `{fname}`\n")
        lines.append("#### Time-Domain Metrics")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        td_keys = ["Mean RR (ms)", "SDNN (ms)", "RMSSD (ms)", "NN50", "pNN50 (%)", "Mean HR (bpm)"]
        for k in td_keys:
            v = m.get(k, "N/A")
            val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
            lines.append(f"| {k} | {val_str} |")
        lines.append("")

        if "LF Power (ms²)" in m:
            lines.append("#### Frequency-Domain Metrics")
            lines.append("| Metric | Value |")
            lines.append("|---|---|")
            fd_keys = ["VLF Power (ms²)", "LF Power (ms²)", "HF Power (ms²)", "LF/HF Ratio", "Total Power (ms²)", "LF norm (%)", "HF norm (%)"]
            for k in fd_keys:
                v = m.get(k, "N/A")
                val_str = f"{v:.3f}" if isinstance(v, float) else str(v)
                lines.append(f"| {k} | {val_str} |")
            lines.append("")

        if "SD1 (ms)" in m:
            lines.append("#### Non-Linear Metrics")
            lines.append("| Metric | Value |")
            lines.append("|---|---|")
            nl_keys = ["SD1 (ms)", "SD2 (ms)", "SD1/SD2", "Ellipse Area (ms²)", "Sample Entropy"]
            for k in nl_keys:
                v = m.get(k, "N/A")
                val_str = f"{v:.3f}" if isinstance(v, float) else str(v)
                lines.append(f"| {k} | {val_str} |")
            lines.append("")

    lines.append("---\n")
    lines.append("## 3. Clinical Interpretation\n")
    for fname, m in metrics_dict.items():
        lines.append(f"### `{fname}`")
        interp = interpret_hrv(m, m)
        lines.append(f"- **Overall HRV (SDNN):** {interp.get('sdnn_class', 'N/A')}")
        lines.append(f"- **Vagal Tone (RMSSD):** {interp.get('autonomic', 'N/A')}")
        lines.append(f"- **Sympathovagal Balance:** {interp.get('lf_hf_class', 'N/A')}\n")

    lines.append("---\n")
    lines.append("## 4. HRV Background & Physiology\n")
    lines.append(
        "Heart Rate Variability (HRV) reflects the variation in time intervals between successive "
        "heartbeats (RR or NN intervals). It is a non-invasive marker of the Autonomic Nervous System (ANS).\n"
    )
    lines.append("**Sympathetic (SNS) activity** increases heart rate and reduces HRV — elevated LF power.")
    lines.append("**Parasympathetic (PNS/vagal) activity** reduces heart rate and increases HRV — elevated HF power.")
    lines.append("The **LF/HF ratio** quantifies the sympathovagal balance:\n")
    lines.append("- LF/HF > 2.0 → Sympathetic dominance (stress, activity, upright posture)")
    lines.append("- LF/HF < 1.0 → Parasympathetic dominance (rest, recovery, sleep)")
    lines.append("- 1.0–2.0    → Balanced autonomic modulation\n")
    lines.append("---\n")
    lines.append("*Report generated by Clinical Sentinel ECG & HRV Analysis Suite.*")
    return "\n".join(lines)


def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Report Generation (CLO3)", badge="Export")
    pipeline_status_bar("HRV")

    metrics_dict = st.session_state.get("metrics", {})
    settings = {k: st.session_state.get(k) for k in
                ["sfreq", "lowcut", "highcut", "remove_baseline", "noise_method",
                 "rpeak_method", "remove_ectopic", "ectopic_threshold", "ectopic_interp",
                 "lf_min", "lf_max", "hf_min", "hf_max"]}

    if not metrics_dict:
        st.warning("No analysis results found. Complete the pipeline first.")
        return

    # ── Report preview ────────────────────────────────────────────────────
    section_header("Report Preview")
    report_md = build_markdown_report(metrics_dict, settings)
    with st.expander("📄 Full Markdown Report Preview", expanded=True):
        st.markdown(report_md)

    st.markdown("---")
    section_header("Downloads")

    col1, col2, col3 = st.columns(3)

    # Markdown download
    with col1:
        st.download_button(
            label="📄 Download Report (.md)",
            data=report_md,
            file_name=f"HRV_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    # CSV metrics
    with col2:
        rows = []
        for f, m in metrics_dict.items():
            row = {"File": f}
            row.update(m)
            rows.append(row)
        df = pd.DataFrame(rows)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            label="📊 Download Metrics (.csv)",
            data=csv_buf.getvalue(),
            file_name=f"HRV_Metrics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Methods section as txt
    with col3:
        methods_txt = (
            "METHODS SUMMARY\n"
            "===============\n\n"
            f"Pipeline: ECG → Preprocessing → R-Peak Detection → RR Intervals → Ectopic Correction → HRV Analysis\n\n"
            f"Filter: {settings.get('lowcut', 0.5)}–{settings.get('highcut', 40)} Hz Butterworth Bandpass\n"
            f"Baseline Removal: {'High-pass @ 0.5 Hz' if settings.get('remove_baseline') else 'Disabled'}\n"
            f"R-Peak Method: {settings.get('rpeak_method', 'NeuroKit')}\n"
            f"Ectopic Detection: Moving-median deviation > {settings.get('ectopic_threshold', 20)}%\n"
            f"Ectopic Correction: {settings.get('ectopic_interp', 'Linear')} Interpolation\n"
            f"PSD: Welch's method, 4 Hz resampled, nperseg=256\n"
            f"LF: {settings.get('lf_min')}–{settings.get('lf_max')} Hz\n"
            f"HF: {settings.get('hf_min')}–{settings.get('hf_max')} Hz\n"
        )
        st.download_button(
            label="📋 Download Methods (.txt)",
            data=methods_txt,
            file_name="HRV_Methods.txt",
            mime="text/plain",
            use_container_width=True
        )

    # ── Per-file interpretation cards ─────────────────────────────────────
    st.markdown("---")
    section_header("Clinical Interpretation Summary")
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        lf_hf = m.get("LF/HF Ratio", float('nan'))
        lf_hf_str = f"{lf_hf:.2f}" if lf_hf == lf_hf else "N/A"
        border_color = "#ffba38" if isinstance(lf_hf, float) and lf_hf > 2 else "#c3f400"
        st.markdown(f"""
        <div style="background:#1a1c1f;border:1px solid #1e2023;border-left:4px solid {border_color};
                    border-radius:0 0.375rem 0.375rem 0;padding:1rem 1.25rem;margin-bottom:0.75rem;">
          <div style="font-family:'Manrope';font-size:0.65rem;font-weight:800;color:#849396;
                      text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;">{fname}</div>
          <div style="font-family:'Inter';font-size:0.8rem;color:#bac9cc;line-height:1.8;">
            <strong style="color:#c3f5ff;">HRV Status:</strong> {interp.get('sdnn_class','—')}<br>
            <strong style="color:#c3f5ff;">Vagal Tone:</strong> {interp.get('autonomic','—')}<br>
            <strong style="color:#c3f5ff;">SNSVS PNS (LF/HF={lf_hf_str}):</strong> {interp.get('lf_hf_class','—')}
          </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
