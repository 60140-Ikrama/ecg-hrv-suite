"""Dashboard (CLO3) — Professional Report Generation with full metrics export"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header, COLORS)
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import interpret_hrv

st.set_page_config(page_title="Report Generation · Clinical Sentinel",
                   page_icon="📑", layout="wide")


# ── report builder ────────────────────────────────────────────────────────────

def build_markdown_report(metrics_dict: dict, settings: dict,
                           sqi_cache: dict) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines += [
        "# Clinical Sentinel — ECG & HRV Analysis Report",
        f"\n**Generated:** {ts}  |  "
        f"**Version:** Research-Grade Suite v2.0\n",
        "---\n",
    ]

    # ── 1. Methodology ────────────────────────────────────────────────────────
    lines += ["## 1. Methodology\n"]
    lines += [
        "### Signal Acquisition",
        f"- Files analysed: {', '.join(metrics_dict.keys())}",
        f"- Sampling frequency: **{settings.get('sfreq', 250):.0f} Hz**\n",
        "### Preprocessing",
        f"- Bandpass filter: **{settings.get('lowcut', 0.5):.2f}–"
        f"{settings.get('highcut', 40):.0f} Hz** "
        f"(Butterworth order {settings.get('filter_order', 4)})",
        f"- Baseline wander removal: "
        f"**{'Yes' if settings.get('remove_baseline', True) else 'No'}**",
        f"- Additional noise filter: **{settings.get('noise_method', 'None')}**\n",
        "### R-Peak Detection",
        f"- Algorithm: **{settings.get('rpeak_method', 'NeuroKit')}**  \n"
        "  *(Pan-Tompkins Custom: implemented from scratch — CLO1)*\n",
        "### Ectopic Beat Correction",
        f"- Enabled: **{'Yes' if settings.get('remove_ectopic', True) else 'No'}**",
        f"- Detection method: **{settings.get('ectopic_method', 'median')}**",
        f"- Detection threshold: **{settings.get('ectopic_threshold', 20)}%**",
        f"- Interpolation: **{settings.get('ectopic_interp', 'Linear')}**\n",
        "### HRV Analysis",
        f"- LF band: **{settings.get('lf_min', 0.04):.2f}–"
        f"{settings.get('lf_max', 0.15):.2f} Hz**",
        f"- HF band: **{settings.get('hf_min', 0.15):.2f}–"
        f"{settings.get('hf_max', 0.40):.2f} Hz**",
        f"- PSD: **Welch's method** (nperseg={settings.get('welch_nperseg', 256)}, "
        f"noverlap={settings.get('welch_noverlap', 128)}, resampled at 4 Hz)\n",
        "### Non-Linear Analysis",
        "- Poincaré plot: SD1, SD2 (short/long-term variability)",
        "- Sample Entropy (SampEn, m=2, r=0.2σ)",
        "- Approximate Entropy (ApEn, m=2, r=0.2σ)",
        f"- Detrended Fluctuation Analysis (DFA): "
        f"**{'Enabled' if settings.get('enable_dfa', True) else 'Disabled'}**  \n"
        "  α1 (4–16 beats) & α2 (16–64 beats) scaling exponents\n",
        "---\n",
    ]

    # ── 2. Results ────────────────────────────────────────────────────────────
    lines += ["## 2. Results\n"]
    for fname, m in metrics_dict.items():
        sqi = sqi_cache.get(fname, {})
        lines += [f"### File: `{fname}`\n"]

        if sqi:
            lines += [
                "#### Signal Quality Index (SQI)",
                "| Metric | Value |",
                "|---|---|",
                f"| Overall SQI | **{sqi.get('overall_sqi','N/A')}/100 — "
                f"{sqi.get('quality_label','—')}** |",
                f"| Spectral SQI | {sqi.get('spectral_sqi','N/A')} |",
                f"| Kurtosis SQI | {sqi.get('kurtosis_sqi','N/A')} |",
                f"| Baseline SQI | {sqi.get('baseline_sqi','N/A')} |",
                f"| Estimated SNR | {sqi.get('snr_db','N/A')} dB |",
                "",
            ]

        lines += [
            "#### Time-Domain Metrics",
            "| Metric | Value |",
            "|---|---|",
        ]
        for k in ["Mean RR (ms)", "SDNN (ms)", "RMSSD (ms)", "SDSD (ms)",
                  "NN50", "pNN50 (%)", "CV (%)", "Mean HR (bpm)"]:
            v = m.get(k, "N/A")
            s = f"{v:.2f}" if isinstance(v, float) else str(v)
            lines.append(f"| {k} | {s} |")
        lines.append("")

        if "LF Power (ms²)" in m:
            lines += [
                "#### Frequency-Domain Metrics",
                "| Metric | Value |",
                "|---|---|",
            ]
            for k in ["VLF Power (ms²)", "LF Power (ms²)", "HF Power (ms²)",
                      "LF/HF Ratio", "Total Power (ms²)",
                      "LF norm (%)", "HF norm (%)"]:
                v = m.get(k, "N/A")
                s = f"{v:.3f}" if isinstance(v, float) else str(v)
                lines.append(f"| {k} | {s} |")
            lines.append("")

        if "SD1 (ms)" in m:
            lines += [
                "#### Non-Linear Metrics",
                "| Metric | Value |",
                "|---|---|",
            ]
            for k in ["SD1 (ms)", "SD2 (ms)", "SD1/SD2",
                      "Ellipse Area (ms²)", "Sample Entropy",
                      "Approx Entropy", "DFA α1", "DFA α2"]:
                v = m.get(k, "N/A")
                s = f"{v:.3f}" if isinstance(v, float) else str(v)
                lines.append(f"| {k} | {s} |")
            lines.append("")

    # ── 3. Clinical Interpretation ────────────────────────────────────────────
    lines += ["---\n", "## 3. Clinical Interpretation\n"]
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        lf_hf  = m.get("LF/HF Ratio", float('nan'))
        a1     = m.get("DFA α1")
        a1_interp = ("N/A" if a1 is None else
                     "Uncorrelated (white noise)" if a1 < 0.5 else
                     "Healthy long-range correlations" if a1 < 1.0 else
                     "1/f (pink) noise" if a1 < 1.5 else
                     "Over-correlated (Brownian noise)")
        lines += [
            f"### `{fname}`",
            f"- **Overall HRV (SDNN):** {interp.get('sdnn_class','N/A')}",
            f"- **Vagal Tone (RMSSD):** {interp.get('autonomic','N/A')}",
            f"- **Sympathovagal Balance:** {interp.get('lf_hf_class','N/A')}",
            f"- **DFA α1 Interpretation:** {a1_interp}\n",
        ]

    # ── 4. HRV Physiology Background ─────────────────────────────────────────
    lines += [
        "---\n",
        "## 4. HRV Background & Physiology\n",
        "Heart Rate Variability (HRV) reflects variation in RR intervals — a "
        "non-invasive marker of Autonomic Nervous System (ANS) function.\n",
        "**Sympathetic (SNS):** increases HR, reduces HRV → elevated LF power.",
        "**Parasympathetic (PNS/vagal):** reduces HR, increases HRV → elevated HF power.",
        "**LF/HF ratio** quantifies sympathovagal balance:\n",
        "| LF/HF | Interpretation |",
        "|---|---|",
        "| > 2.0 | Sympathetic dominance (stress, activity, upright posture) |",
        "| 1.0–2.0 | Balanced autonomic modulation |",
        "| < 1.0 | Parasympathetic dominance (rest, recovery, sleep) |\n",
        "**DFA α1 reference ranges:**\n",
        "| α1 Range | Interpretation |",
        "|---|---|",
        "| < 0.5 | Uncorrelated (white noise) — very low HRV |",
        "| 0.5–1.0 | Long-range correlations — normal/healthy |",
        "| ≈ 1.0 | 1/f (pink noise) — optimal cardiac complexity |",
        "| > 1.5 | Over-correlated (Brownian noise) — pathological |",
        "",
        "---\n",
        "*Report generated by Clinical Sentinel ECG & HRV Analysis Suite v2.0*  \n"
        "*Algorithms: Pan-Tompkins (custom), Welch PSD, DFA, SampEn, ApEn, Poincaré (CLO1 & CLO2)*",
    ]
    return "\n".join(lines)


# ── Chart & Document Generators ───────────────────────────────────────────────

def _generate_report_charts(filename: str) -> dict:
    import plotly.graph_objects as go
    import numpy as np
    from components.theme import COLORS, PLOTLY_LAYOUT
    charts = {}
    
    # 1. ECG
    sig = st.session_state.get("cleaned_signals", {}).get(filename)
    if sig is None: sig = st.session_state.get("raw_signals", {}).get(filename)
    sfreq = st.session_state.get("sfreq", 250.0)
    if sig is not None:
        t = np.arange(len(sig)) / sfreq
        max_idx = min(len(sig), int(10 * sfreq))
        fig_ecg = go.Figure()
        fig_ecg.add_trace(go.Scatter(x=t[:max_idx], y=sig[:max_idx], line=dict(color=COLORS["primary"])))
        fig_ecg.update_layout(**{**PLOTLY_LAYOUT, "title": "ECG Waveform (First 10s)", "showlegend": False})
        try: charts["ecg"] = fig_ecg.to_image(format="png", width=800, height=350, engine="kaleido")
        except: pass
        
    # 2. Tachogram
    rr = st.session_state.get("clean_rr_intervals", {}).get(filename)
    if rr is not None and len(rr) > 0:
        fig_rr = go.Figure()
        fig_rr.add_trace(go.Scatter(y=rr, mode='lines+markers', line=dict(color=COLORS["primary_dim"])))
        fig_rr.update_layout(**{**PLOTLY_LAYOUT, "title": "RR Interval Tachogram", "showlegend": False})
        try: charts["rr"] = fig_rr.to_image(format="png", width=800, height=350, engine="kaleido")
        except: pass
        
    # 3. PSD
    psd_raw = st.session_state.get("psd_data", {}).get(filename)
    if psd_raw is not None:
        try:
            freqs_p, psd_p = psd_raw
            fig_psd = go.Figure()
            fig_psd.add_trace(go.Scatter(x=freqs_p, y=psd_p, fill="tozeroy",
                                         line=dict(color=COLORS["secondary_fixed"])))
            fig_psd.update_layout(**{**PLOTLY_LAYOUT, "title": "Welch PSD", "showlegend": False})
            charts["psd"] = fig_psd.to_image(format="png", width=800, height=350, engine="kaleido")
        except Exception as _e:
            print("PSD chart err:", _e)
        
    # Poincare plot
    rr_pc = st.session_state.get("clean_rr_intervals", {}).get(filename)
    if rr_pc is not None and len(rr_pc) > 2:
        try:
            rn, rn1 = rr_pc[:-1], rr_pc[1:]
            fig_pc = go.Figure()
            fig_pc.add_trace(go.Scatter(x=rn, y=rn1, mode="markers",
                                        marker=dict(color=COLORS["primary_dim"], size=4, opacity=0.5)))
            fig_pc.update_layout(**{**PLOTLY_LAYOUT, "title": "Poincare Plot", "showlegend": False})
            charts["poincare"] = fig_pc.to_image(format="png", width=600, height=600, engine="kaleido")
        except Exception as _e:
            print("Poincare chart error:", _e)

    # R-peaks chart
    sig2 = st.session_state.get("cleaned_signals", {}).get(filename)
    rpeaks2 = st.session_state.get("rpeaks", {}).get(filename)
    if sig2 is not None and rpeaks2 is not None and len(rpeaks2):
        try:
            sfreq2 = st.session_state.get("sfreq", 250.0)
            t2 = np.arange(len(sig2)) / sfreq2
            mx = min(len(sig2), int(10 * sfreq2))
            fig_rp = go.Figure()
            fig_rp.add_trace(go.Scatter(x=t2[:mx], y=sig2[:mx], mode="lines",
                                        line=dict(color=COLORS["secondary_fixed"], width=1)))
            rp_in = rpeaks2[rpeaks2 < mx]
            fig_rp.add_trace(go.Scatter(x=rp_in / sfreq2, y=sig2[rp_in], mode="markers",
                                        marker=dict(color=COLORS["error"], size=8, symbol="triangle-up")))
            fig_rp.update_layout(**{**PLOTLY_LAYOUT, "title": "R-Peak Detection", "showlegend": False})
            charts["rpeaks"] = fig_rp.to_image(format="png", width=800, height=350, engine="kaleido")
        except Exception as _e:
            print("R-peaks chart error:", _e)

    # Poincare plot
    rr_pc = st.session_state.get("clean_rr_intervals", {}).get(filename)
    if rr_pc is not None and len(rr_pc) > 2:
        try:
            rn, rn1 = rr_pc[:-1], rr_pc[1:]
            fig_pc = go.Figure()
            fig_pc.add_trace(go.Scatter(x=rn.tolist(), y=rn1.tolist(), mode="markers",
                marker=dict(color=COLORS["primary_dim"], size=4, opacity=0.5)))
            fig_pc.update_layout(**{**PLOTLY_LAYOUT, "title": "Poincare Plot", "showlegend": False})
            charts["poincare"] = fig_pc.to_image(format="png", width=600, height=600, engine="kaleido")
        except Exception as _e:
            print("Poincare err:", _e)
    # R-peaks chart
    sig2 = st.session_state.get("cleaned_signals", {}).get(filename)
    rpeaks2 = st.session_state.get("rpeaks", {}).get(filename)
    if sig2 is not None and rpeaks2 is not None and len(rpeaks2):
        try:
            sfreq2 = st.session_state.get("sfreq", 250.0)
            t2 = np.arange(len(sig2)) / sfreq2
            mx = min(len(sig2), int(10 * sfreq2))
            rp_in = rpeaks2[rpeaks2 < mx]
            fig_rp = go.Figure()
            fig_rp.add_trace(go.Scatter(x=t2[:mx].tolist(), y=sig2[:mx].tolist(),
                mode="lines", line=dict(color=COLORS["secondary_fixed"], width=1)))
            fig_rp.add_trace(go.Scatter(x=(rp_in/sfreq2).tolist(), y=sig2[rp_in].tolist(),
                mode="markers", marker=dict(color=COLORS["error"], size=8, symbol="triangle-up")))
            fig_rp.update_layout(**{**PLOTLY_LAYOUT, "title": "R-Peak Detection", "showlegend": False})
            charts["rpeaks"] = fig_rp.to_image(format="png", width=800, height=350, engine="kaleido")
        except Exception as _e:
            print("R-peaks err:", _e)
        return charts

def _safe(v):
    """Format metric value safely."""
    if isinstance(v, float):
        return f"{v:.3f}"
    if v is None:
        return "N/A"
    return str(v)


def build_pdf_report(metrics_dict: dict, settings: dict, sqi_cache: dict) -> bytes:
    import io as _io
    import tempfile, os as _os
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, Image as RLImage, PageBreak)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register a Unicode-capable font (Windows system fonts first, then matplotlib DejaVu)
    import pathlib as _pl
    BODY_FONT, BOLD_FONT = "Helvetica", "Helvetica-Bold"  # safe fallback
    _font_candidates = [
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\times.ttf",
    ]
    # Also try matplotlib bundled DejaVu
    try:
        import matplotlib
        _mpl_fonts = _pl.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        for _f in _mpl_fonts.glob("DejaVuSans*.ttf"):
            _font_candidates.insert(0, str(_f))
    except Exception:
        pass
    for _fp in _font_candidates:
        try:
            pdfmetrics.registerFont(TTFont("UniFont", _fp))
            BODY_FONT, BOLD_FONT = "UniFont", "UniFont"
            break
        except Exception:
            continue

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", fontName=BOLD_FONT, fontSize=18, spaceAfter=8,
                         textColor=rl_colors.HexColor("#003366"), leading=22)
    h2 = ParagraphStyle("h2", fontName=BOLD_FONT, fontSize=13, spaceAfter=6,
                         textColor=rl_colors.HexColor("#1a5276"), leading=16)
    h3 = ParagraphStyle("h3", fontName=BOLD_FONT, fontSize=11, spaceAfter=4,
                         textColor=rl_colors.HexColor("#2e86c1"), leading=14)
    body = ParagraphStyle("body", fontName=BODY_FONT, fontSize=9,
                           spaceAfter=4, leading=13)

    tbl_style = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), rl_colors.HexColor("#1a5276")),
        ("TEXTCOLOR",   (0,0), (-1,0), rl_colors.white),
        ("FONTNAME",    (0,0), (-1,0), BOLD_FONT),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("FONTNAME",    (0,1), (-1,-1), BODY_FONT),
        ("BACKGROUND",  (0,1), (-1,-1), rl_colors.HexColor("#eaf4fc")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [rl_colors.HexColor("#eaf4fc"), rl_colors.HexColor("#d6eaf8")]),
        ("GRID",        (0,0), (-1,-1), 0.4, rl_colors.HexColor("#aed6f1")),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ])

    story = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Title page ────────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Sentinel", h1))
    story.append(Paragraph("ECG &amp; HRV Analysis Report", h1))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Generated: {ts}", body))
    story.append(Paragraph("Research-Grade Suite v2.0  |  CLO2 &amp; CLO3", body))
    story.append(Spacer(1, 0.5*cm))

    # ── Methodology ───────────────────────────────────────────────────────
    story.append(Paragraph("1. Methodology", h2))
    fnames_str = ", ".join(metrics_dict.keys())
    meth_rows = [
        ["Parameter", "Value"],
        ["Files analysed", fnames_str],
        ["Sampling frequency", f"{settings.get('sfreq', 250):.0f} Hz"],
        ["Bandpass filter", f"{settings.get('lowcut', 0.5):.2f}-{settings.get('highcut', 40):.0f} Hz"],
        ["Filter order", str(settings.get('filter_order', 4))],
        ["R-Peak algorithm", str(settings.get('rpeak_method', 'NeuroKit'))],
        ["Ectopic detection", str(settings.get('ectopic_method', 'median'))],
        ["LF band", f"{settings.get('lf_min', 0.04):.2f}-{settings.get('lf_max', 0.15):.2f} Hz"],
        ["HF band", f"{settings.get('hf_min', 0.15):.2f}-{settings.get('hf_max', 0.40):.2f} Hz"],
        ["PSD method", "Welch"],
        ["Non-linear", "Poincare, SampEn, ApEn, DFA alpha1/alpha2"],
    ]
    t = Table(meth_rows, colWidths=[5*cm, 11*cm])
    t.setStyle(tbl_style)
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ── Per-file results ───────────────────────────────────────────────────
    story.append(Paragraph("2. Results", h2))

    for fname, m in metrics_dict.items():
        story.append(Paragraph(f"File: {fname}", h3))

        # Time-domain table
        td_rows = [["Metric", "Value"],
                   ["Mean RR (ms)",  _safe(m.get("Mean RR (ms)"))],
                   ["Mean HR (bpm)", _safe(m.get("Mean HR (bpm)"))],
                   ["SDNN (ms)",     _safe(m.get("SDNN (ms)"))],
                   ["RMSSD (ms)",    _safe(m.get("RMSSD (ms)"))],
                   ["SDSD (ms)",     _safe(m.get("SDSD (ms)"))],
                   ["NN50",          _safe(m.get("NN50"))],
                   ["pNN50 (%)",     _safe(m.get("pNN50 (%)"))],
                   ["CV (%)",        _safe(m.get("CV (%)"))]]
        story.append(Paragraph("Time-Domain HRV Metrics", h3))
        t1 = Table(td_rows, colWidths=[7*cm, 9*cm])
        t1.setStyle(tbl_style)
        story.append(t1)
        story.append(Spacer(1, 0.3*cm))

        # Frequency-domain table
        if "LF Power (ms2)" in m or "LF Power (ms²)" in m:
            lf_key  = "LF Power (ms²)" if "LF Power (ms²)" in m else "LF Power (ms2)"
            hf_key  = "HF Power (ms²)" if "HF Power (ms²)" in m else "HF Power (ms2)"
            vlf_key = "VLF Power (ms²)" if "VLF Power (ms²)" in m else "VLF Power (ms2)"
            tp_key  = "Total Power (ms²)" if "Total Power (ms²)" in m else "Total Power (ms2)"
            fd_rows = [["Metric", "Value"],
                       ["VLF Power (ms2)", _safe(m.get(vlf_key))],
                       ["LF Power (ms2)",  _safe(m.get(lf_key))],
                       ["HF Power (ms2)",  _safe(m.get(hf_key))],
                       ["LF/HF Ratio",     _safe(m.get("LF/HF Ratio"))],
                       ["Total Power",     _safe(m.get(tp_key))],
                       ["LF norm (%)",     _safe(m.get("LF norm (%)"))],
                       ["HF norm (%)",     _safe(m.get("HF norm (%)"))]]
            story.append(Paragraph("Frequency-Domain HRV Metrics", h3))
            t2 = Table(fd_rows, colWidths=[7*cm, 9*cm])
            t2.setStyle(tbl_style)
            story.append(t2)
            story.append(Spacer(1, 0.3*cm))

        # Non-linear table
        if "SD1 (ms)" in m:
            nl_rows = [["Metric", "Value"],
                       ["SD1 (ms)",           _safe(m.get("SD1 (ms)"))],
                       ["SD2 (ms)",           _safe(m.get("SD2 (ms)"))],
                       ["SD1/SD2",            _safe(m.get("SD1/SD2"))],
                       ["Sample Entropy",     _safe(m.get("Sample Entropy"))],
                       ["Approx Entropy",     _safe(m.get("Approx Entropy"))],
                       ["DFA alpha1",         _safe(m.get("DFA α1") or m.get("DFA alpha1"))],
                       ["DFA alpha2",         _safe(m.get("DFA α2") or m.get("DFA alpha2"))]]
            story.append(Paragraph("Non-Linear HRV Metrics", h3))
            t3 = Table(nl_rows, colWidths=[7*cm, 9*cm])
            t3.setStyle(tbl_style)
            story.append(t3)
            story.append(Spacer(1, 0.3*cm))

        # Charts
        story.append(Paragraph("Signal Visualisations", h3))
        charts = _generate_report_charts(fname)
        chart_labels = {
            "ecg":     "ECG Waveform (first 10 s)",
            "rpeaks":  "R-Peak Detection",
            "rr":      "RR Interval Tachogram",
            "psd":     "Power Spectral Density (Welch)",
            "poincare":"Poincare Plot",
        }
        for ckey, cbytes in charts.items():
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmp.write(cbytes); tmp.close()
                w = 14*cm if ckey == "poincare" else 16*cm
                story.append(Paragraph(chart_labels.get(ckey, ckey), body))
                story.append(RLImage(tmp.name, width=w, height=w*0.45 if ckey != "poincare" else w))
                story.append(Spacer(1, 0.3*cm))
                _os.unlink(tmp.name)
            except Exception:
                pass

        story.append(PageBreak())

    # ── Interpretation ────────────────────────────────────────────────────
    story.append(Paragraph("3. Clinical Interpretation", h2))
    from utils.hrv_analysis import interpret_hrv
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        lf_hf  = m.get("LF/HF Ratio")
        a1     = m.get("DFA α1") or m.get("DFA alpha1")
        story.append(Paragraph(f"File: {fname}", h3))
        rows = [["Assessment", "Result"],
                ["HRV Status (SDNN)",      interp.get("sdnn_class", "N/A")],
                ["Vagal Tone (RMSSD)",     interp.get("autonomic",  "N/A")],
                ["Sympathovagal (LF/HF)",  interp.get("lf_hf_class","N/A")],
                ["LF/HF Value",            _safe(lf_hf)],
                ["DFA alpha1",             _safe(a1)]]
        ti = Table(rows, colWidths=[7*cm, 9*cm])
        ti.setStyle(tbl_style)
        story.append(ti)
        story.append(Spacer(1, 0.4*cm))

    # ── Physiology background ─────────────────────────────────────────────
    story.append(Paragraph("4. HRV Physiology Background", h2))
    bg_rows = [["LF/HF Ratio", "Interpretation"],
               ["> 2.0",  "Sympathetic dominance (stress / upright posture)"],
               ["1.0-2.0","Balanced autonomic modulation"],
               ["< 1.0",  "Parasympathetic dominance (rest / recovery)"]]
    tb = Table(bg_rows, colWidths=[4*cm, 12*cm])
    tb.setStyle(tbl_style)
    story.append(tb)
    story.append(Spacer(1, 0.3*cm))
    dfa_rows = [["DFA alpha1 Range", "Interpretation"],
                ["< 0.5",  "Uncorrelated (white noise) - very low HRV"],
                ["0.5-1.0","Long-range correlations - healthy HRV"],
                ["~1.0",   "1/f (pink noise) - optimal cardiac complexity"],
                ["> 1.5",  "Over-correlated (Brownian noise) - pathological"]]
    td2 = Table(dfa_rows, colWidths=[4*cm, 12*cm])
    td2.setStyle(tbl_style)
    story.append(td2)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Report generated by Clinical Sentinel ECG &amp; HRV Analysis Suite v2.0  |  "
        "Algorithms: Pan-Tompkins (custom), Welch PSD, DFA, SampEn, ApEn, Poincare (CLO1 &amp; CLO2)",
        body))

    doc.build(story)
    return buf.getvalue()

def build_docx_report(metrics_dict: dict, settings: dict, sqi_cache: dict) -> bytes:
    import docx
    from docx.shared import Inches
    import io
    doc = docx.Document()
    doc.add_heading("Clinical Sentinel - ECG & HRV Analysis Report", 0)
    doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for fname, m in metrics_dict.items():
        doc.add_heading(f"File: {fname}", level=1)
        
        doc.add_heading("Key Metrics", level=2)
        table = doc.add_table(rows=1, cols=2)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Metric"
        hdr_cells[1].text = "Value"
        for k in ["Mean HR (bpm)", "SDNN (ms)", "RMSSD (ms)", "LF/HF Ratio", "DFA α1"]:
            if k in m:
                v = m[k]
                s = f"{v:.2f}" if isinstance(v, float) else str(v)
                row_cells = table.add_row().cells
                row_cells[0].text = k
                row_cells[1].text = s
                
        # Embed Charts
        charts = _generate_report_charts(fname)
        for cname, cbytes in charts.items():
            doc.add_picture(io.BytesIO(cbytes), width=Inches(6.0))
            
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Report Generation (CLO2 & CLO3)", badge="Export")
    pipeline_status_bar("HRV")

    metrics_dict = st.session_state.get("metrics",   {})
    sqi_cache    = st.session_state.get("sqi_cache", {})
    settings     = {k: st.session_state.get(k) for k in [
        "sfreq", "lowcut", "highcut", "remove_baseline", "noise_method",
        "filter_order", "rpeak_method", "remove_ectopic", "ectopic_threshold",
        "ectopic_method", "ectopic_interp", "lf_min", "lf_max", "hf_min", "hf_max",
        "welch_nperseg", "welch_noverlap", "enable_dfa",
    ]}

    if not metrics_dict:
        st.warning("No analysis results found. Complete the pipeline first.")
        return

    # ── Report preview ────────────────────────────────────────────────────────
    section_header("Report Preview")
    report_md = build_markdown_report(metrics_dict, settings, sqi_cache)
    with st.expander("📄 Full Markdown Report Preview", expanded=True):
        st.markdown(report_md)

    st.markdown("---")
    section_header("Rich Document Export (CLO3)")
    st.markdown('<div style="font-size:0.8rem;color:#849396;margin-bottom:1rem;">Generates comprehensive documents with embedded Plotly visualisations (ECG, Tachogram, PSD, Poincaré).</div>', unsafe_allow_html=True)
    
    col_pdf, col_docx, _ = st.columns([1, 1, 2])
    with col_pdf:
        if st.button("📄 Render PDF Report", use_container_width=True):
            with st.spinner("Generating PDF (may take a few seconds)..."):
                try:
                    st.session_state["pdf_bytes"] = build_pdf_report(metrics_dict, settings, sqi_cache)
                except Exception as e:
                    st.error(f"Failed: {e}")
        if "pdf_bytes" in st.session_state:
            st.download_button("⬇️ Download PDF", data=st.session_state["pdf_bytes"], file_name=f"HRV_Report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)
            
    with col_docx:
        if st.button("📘 Render DOCX Report", use_container_width=True):
            with st.spinner("Generating Word Document..."):
                try:
                    st.session_state["docx_bytes"] = build_docx_report(metrics_dict, settings, sqi_cache)
                except Exception as e:
                    st.error(f"Failed: {e}")
        if "docx_bytes" in st.session_state:
            st.download_button("⬇️ Download DOCX", data=st.session_state["docx_bytes"], file_name=f"HRV_Report_{datetime.now().strftime('%Y%m%d')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    st.markdown("---")
    section_header("Raw Data Downloads")

    col1, col2, col3 = st.columns(3)

    # Markdown download
    with col1:
        st.download_button(
            label="📄 Download Report (.md)",
            data=report_md,
            file_name=f"HRV_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True)

    # CSV metrics
    with col2:
        rows = []
        for f, m in metrics_dict.items():
            row = {"File": f}
            row.update(m)
            sqi = sqi_cache.get(f, {})
            if sqi:
                row["SQI overall"] = sqi.get("overall_sqi")
                row["SQI label"]   = sqi.get("quality_label")
                row["SNR (dB)"]    = sqi.get("snr_db")
            rows.append(row)
        df = pd.DataFrame(rows)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button(
            label="📊 Download Metrics (.csv)",
            data=buf.getvalue(),
            file_name=f"HRV_Metrics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True)

    # Methods text
    with col3:
        methods_txt = (
            "METHODS SUMMARY\n"
            "===============\n\n"
            f"Pipeline: ECG → Preprocessing → R-Peak → RR Intervals "
            f"→ Ectopic Correction → HRV Analysis\n\n"
            f"Filter       : {settings.get('lowcut')}–{settings.get('highcut')} Hz "
            f"Butterworth order {settings.get('filter_order', 4)}\n"
            f"Baseline     : {'High-pass @ 0.5 Hz' if settings.get('remove_baseline') else 'Disabled'}\n"
            f"R-Peak       : {settings.get('rpeak_method')} "
            f"(Pan-Tompkins Custom: from-scratch CLO1 implementation)\n"
            f"Ectopic Det. : {settings.get('ectopic_method')} deviation > "
            f"{settings.get('ectopic_threshold')}%\n"
            f"Ectopic Corr.: {settings.get('ectopic_interp')} interpolation\n"
            f"PSD          : Welch, 4 Hz resample, nperseg={settings.get('welch_nperseg')}, "
            f"noverlap={settings.get('welch_noverlap')}\n"
            f"LF band      : {settings.get('lf_min')}–{settings.get('lf_max')} Hz\n"
            f"HF band      : {settings.get('hf_min')}–{settings.get('hf_max')} Hz\n"
            f"DFA          : {'α1 (4–16 beats), α2 (16–64 beats)' if settings.get('enable_dfa') else 'Disabled'}\n"
            f"Entropy      : SampEn & ApEn (m=2, r=0.2σ, max 300 beats)\n"
        )
        st.download_button(
            label="📋 Download Methods (.txt)",
            data=methods_txt,
            file_name="HRV_Methods.txt",
            mime="text/plain",
            use_container_width=True)

    # ── Per-file interpretation cards ─────────────────────────────────────────
    st.markdown("---")
    section_header("Clinical Interpretation Summary")
    for fname, m in metrics_dict.items():
        interp  = interpret_hrv(m, m)
        sqi     = sqi_cache.get(fname, {})
        lf_hf   = m.get("LF/HF Ratio", float('nan'))
        a1      = m.get("DFA α1")
        sqi_lbl = sqi.get("quality_label", "—") if sqi else "—"
        sqi_clr = ("#c3f400" if sqi_lbl == "Excellent" else
                   "#00daf3" if sqi_lbl == "Good" else
                   "#ffba38" if sqi_lbl == "Acceptable" else
                   "#ffb4ab" if sqi_lbl == "Poor" else "#849396")
        border  = ("#ffba38" if isinstance(lf_hf, float) and lf_hf > 2
                   else "#c3f400")
        lf_hf_s = f"{lf_hf:.2f}" if (isinstance(lf_hf, float) and lf_hf == lf_hf) else "N/A"
        a1_s    = f"{a1:.3f}" if isinstance(a1, float) else "N/A"
        st.markdown(f"""
        <div style="background:#1a1c1f;border:1px solid #1e2023;
                    border-left:4px solid {border};
                    border-radius:0 0.375rem 0.375rem 0;
                    padding:1rem 1.25rem;margin-bottom:0.75rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;
                      margin-bottom:0.4rem;">
            <span style="font-family:'Manrope';font-size:0.65rem;font-weight:800;
                         color:#849396;text-transform:uppercase;letter-spacing:0.1em;">
              {fname}</span>
            <span style="background:{sqi_clr};color:#000;font-family:Manrope;
                         font-size:0.6rem;font-weight:800;padding:0.15rem 0.5rem;
                         border-radius:0.2rem;text-transform:uppercase;">
              SQI: {sqi_lbl}</span>
          </div>
          <div style="font-family:'Inter';font-size:0.8rem;color:#bac9cc;line-height:1.9;">
            <strong style="color:#c3f5ff;">HRV Status:</strong>
            {interp.get('sdnn_class','—')}<br>
            <strong style="color:#c3f5ff;">Vagal Tone:</strong>
            {interp.get('autonomic','—')}<br>
            <strong style="color:#c3f5ff;">Sympathovagal (LF/HF={lf_hf_s}):</strong>
            {interp.get('lf_hf_class','—')}<br>
            <strong style="color:#c3f5ff;">DFA α1={a1_s}:</strong>
            {'Healthy long-range correlations' if isinstance(a1, float) and 0.5 <= a1 < 1.0 else
             'Review fractal complexity — outside healthy range' if isinstance(a1, float) else
             'Not computed'}
          </div>
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
