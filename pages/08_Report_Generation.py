"""Dashboard (CLO3) — Professional Report Generation with full metrics export"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import sys, os
import numpy as np
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import (inject_stitch_theme, sentinel_header,
                               pipeline_status_bar, section_header, COLORS, PLOTLY_LAYOUT)
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

        if "LF Power (ms²)" in m or "LF Power (ms2)" in m:
            lines += [
                "#### Frequency-Domain Metrics",
                "| Metric | Value |",
                "|---|---|",
            ]
            for k in ["VLF Power (ms²)", "LF Power (ms²)", "HF Power (ms²)",
                      "LF/HF Ratio", "Total Power (ms²)",
                      "LF norm (%)", "HF norm (%)"]:
                k_lookup = k.replace("²", "2") if k not in m else k
                v = m.get(k_lookup, "N/A")
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
                k_lookup = k.replace("α", "alpha").replace("²", "2") if k not in m else k
                v = m.get(k_lookup, "N/A")
                s = f"{v:.3f}" if isinstance(v, float) else str(v)
                lines.append(f"| {k} | {s} |")
            lines.append("")

    # ── 3. Clinical Interpretation ────────────────────────────────────────────
    lines += ["---\n", "## 3. Clinical Interpretation\n"]
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        lf_hf  = m.get("LF/HF Ratio", float('nan'))
        a1     = m.get("DFA α1") or m.get("DFA alpha1")
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
        except Exception as e: print(f"ECG chart err: {e}")
        
    # 2. Tachogram
    rr = st.session_state.get("clean_rr_intervals", {}).get(filename)
    if rr is not None and len(rr) > 0:
        fig_rr = go.Figure()
        fig_rr.add_trace(go.Scatter(y=rr, mode='lines+markers', line=dict(color=COLORS["primary_dim"])))
        fig_rr.update_layout(**{**PLOTLY_LAYOUT, "title": "RR Interval Tachogram", "showlegend": False})
        try: charts["rr"] = fig_rr.to_image(format="png", width=800, height=350, engine="kaleido")
        except Exception as e: print(f"RR chart err: {e}")
        
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
        except Exception as e: print(f"PSD chart err: {e}")
        
    # 4. Poincare plot
    if rr is not None and len(rr) > 2:
        try:
            rn, rn1 = rr[:-1], rr[1:]
            fig_pc = go.Figure()
            fig_pc.add_trace(go.Scatter(x=rn, y=rn1, mode="markers",
                                        marker=dict(color=COLORS["primary_dim"], size=4, opacity=0.5)))
            fig_pc.update_layout(**{**PLOTLY_LAYOUT, "title": "Poincare Plot", "showlegend": False})
            charts["poincare"] = fig_pc.to_image(format="png", width=600, height=600, engine="kaleido")
        except Exception as e: print(f"Poincare chart error: {e}")

    # 5. R-peaks chart
    rpeaks = st.session_state.get("rpeaks", {}).get(filename)
    if sig is not None and rpeaks is not None and len(rpeaks) > 0:
        try:
            t_sig = np.arange(len(sig)) / sfreq
            max_idx = min(len(sig), int(10 * sfreq))
            fig_rp = go.Figure()
            fig_rp.add_trace(go.Scatter(x=t_sig[:max_idx], y=sig[:max_idx], mode="lines",
                                        line=dict(color=COLORS["secondary_fixed"], width=1)))
            rp_in = rpeaks[rpeaks < max_idx]
            fig_rp.add_trace(go.Scatter(x=rp_in / sfreq, y=sig[rp_in], mode="markers",
                                        marker=dict(color=COLORS["error"], size=8, symbol="triangle-up")))
            fig_rp.update_layout(**{**PLOTLY_LAYOUT, "title": "R-Peak Detection", "showlegend": False})
            charts["rpeaks"] = fig_rp.to_image(format="png", width=800, height=350, engine="kaleido")
        except Exception as e: print(f"R-peaks chart error: {e}")

    return charts

def _safe(v):
    """Format metric value safely."""
    if isinstance(v, (float, np.float64, np.float32)):
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

    # Register a Unicode-capable font
    import pathlib as _pl
    BODY_FONT, BOLD_FONT = "Helvetica", "Helvetica-Bold"  # fallback
    _font_candidates = []
    
    # Priority 1: Matplotlib fonts (very reliable if matplotlib is present)
    try:
        import matplotlib
        _mpl_fonts = _pl.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        for _f in _mpl_fonts.glob("DejaVuSans*.ttf"):
            _font_candidates.append(str(_f))
    except Exception: pass

    # Priority 2: Windows system fonts
    _win_fonts = [
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\times.ttf",
    ]
    _font_candidates.extend(_win_fonts)

    for _fp in _font_candidates:
        if _os.path.exists(_fp):
            try:
                font_name = "UniFont_" + _os.path.basename(_fp).split('.')[0]
                pdfmetrics.registerFont(TTFont(font_name, _fp))
                BODY_FONT = font_name
                BOLD_FONT = font_name
                break
            except Exception: continue

    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", fontName=BOLD_FONT, fontSize=18, spaceAfter=12, textColor=rl_colors.HexColor("#003366"))
    h2 = ParagraphStyle("h2", fontName=BOLD_FONT, fontSize=14, spaceAfter=10, textColor=rl_colors.HexColor("#1a5276"), spaceBefore=10)
    h3 = ParagraphStyle("h3", fontName=BOLD_FONT, fontSize=12, spaceAfter=8, textColor=rl_colors.HexColor("#2e86c1"), spaceBefore=8)
    body = ParagraphStyle("body", fontName=BODY_FONT, fontSize=10, spaceAfter=6, leading=12)

    tbl_style = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#1a5276")),
        ("TEXTCOLOR", (0,0), (-1,0), rl_colors.white),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTNAME", (0,0), (-1,0), BOLD_FONT),
        ("FONTSIZE", (0,0), (-1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("BACKGROUND", (0,1), (-1,-1), rl_colors.HexColor("#f0f7fa")),
        ("TEXTCOLOR", (0,1), (-1,-1), rl_colors.black),
        ("FONTNAME", (0,1), (-1,-1), BODY_FONT),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("GRID", (0,0), (-1,-1), 0.5, rl_colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ])

    story = []
    story.append(Paragraph("Clinical Sentinel — ECG & HRV Analysis Report", h1))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body))
    story.append(Paragraph("Version: Research-Grade Suite v2.0", body))
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("1. Methodology", h2))
    meth_data = [
        ["Parameter", "Value"],
        ["Files analysed", ", ".join(metrics_dict.keys())],
        ["Sampling Frequency", f"{settings.get('sfreq', 250):.0f} Hz"],
        ["Bandpass Filter", f"{settings.get('lowcut', 0.5):.2f}–{settings.get('highcut', 40):.0f} Hz"],
        ["R-Peak Algorithm", str(settings.get('rpeak_method', 'NeuroKit'))],
        ["Ectopic Correction", "Enabled" if settings.get('remove_ectopic', True) else "Disabled"],
        ["PSD Method", "Welch"],
    ]
    tm = Table(meth_data, colWidths=[6*cm, 12*cm])
    tm.setStyle(tbl_style)
    story.append(tm)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("2. Results", h2))

    for fname, m in metrics_dict.items():
        story.append(Paragraph(f"File: {fname}", h3))
        story.append(Paragraph("Time-Domain Metrics", body))
        td_data = [["Metric", "Value"]]
        for k in ["Mean RR (ms)", "SDNN (ms)", "RMSSD (ms)", "Mean HR (bpm)", "pNN50 (%)"]:
            td_data.append([k, _safe(m.get(k))])
        ttd = Table(td_data, colWidths=[9*cm, 9*cm])
        ttd.setStyle(tbl_style)
        story.append(ttd)
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("Frequency-Domain Metrics", body))
        fd_data = [["Metric", "Value"]]
        for k in ["LF Power (ms2)", "HF Power (ms2)", "LF/HF Ratio", "LF norm (%)", "HF norm (%)"]:
            k_lookup = k.replace("2", "²") if k not in m else k
            fd_data.append([k.replace("2", "²"), _safe(m.get(k_lookup))])
        tfd = Table(fd_data, colWidths=[9*cm, 9*cm])
        tfd.setStyle(tbl_style)
        story.append(tfd)
        story.append(Spacer(1, 0.3*cm))

        charts = _generate_report_charts(fname)
        for ckey in ["ecg", "rpeaks", "rr", "psd", "poincare"]:
            if ckey in charts:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(charts[ckey])
                        tmp_path = tmp.name
                    story.append(Paragraph(ckey.upper() + " Visualization", body))
                    img_w = 16*cm if ckey != "poincare" else 12*cm
                    img_h = 7*cm if ckey != "poincare" else 12*cm
                    story.append(RLImage(tmp_path, width=img_w, height=img_h))
                    story.append(Spacer(1, 0.3*cm))
                    _os.remove(tmp_path)
                except Exception as e:
                    print(f"Failed to add image {ckey}: {e}")

        story.append(PageBreak())

    story.append(Paragraph("3. Clinical Interpretation", h2))
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        story.append(Paragraph(f"Analysis for {fname}:", h3))
        story.append(Paragraph(f"• Overall HRV (SDNN): {interp.get('sdnn_class','N/A')}", body))
        story.append(Paragraph(f"• Vagal Tone (RMSSD): {interp.get('autonomic','N/A')}", body))
        story.append(Paragraph(f"• Sympathovagal Balance: {interp.get('lf_hf_class','N/A')}", body))
        story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return buf.getvalue()


def build_docx_report(metrics_dict: dict, settings: dict, sqi_cache: dict) -> bytes:
    import docx
    from docx.shared import Inches, Pt
    import io
    doc = docx.Document()
    
    doc.add_heading("ECG-HRV Analysis Report", 0)
    doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph(
        "This report provides a comprehensive analysis of Electrocardiogram (ECG) data and "
        "Heart Rate Variability (HRV) metrics. HRV is a non-invasive marker of autonomic "
        "nervous system function, reflecting the balance between sympathetic and "
        "parasympathetic activity."
    )
    
    doc.add_heading("Methodology", level=1)
    doc.add_paragraph(f"Files analysed: {', '.join(metrics_dict.keys())}")
    doc.add_paragraph(f"Sampling frequency: {settings.get('sfreq', 250):.0f} Hz")
    doc.add_paragraph(
        f"Preprocessing: Bandpass filter ({settings.get('lowcut', 0.5):.2f}–{settings.get('highcut', 40):.0f} Hz), "
        f"Baseline wander removal ({'Yes' if settings.get('remove_baseline', True) else 'No'})."
    )
    doc.add_paragraph(f"R-Peak Detection Algorithm: {settings.get('rpeak_method', 'NeuroKit')}")
    doc.add_paragraph(f"Ectopic Correction: {'Enabled' if settings.get('remove_ectopic', True) else 'Disabled'}")
    doc.add_paragraph("Frequency-Domain Analysis: Welch's Periodogram.")
    
    doc.add_heading("Results", level=1)
    for fname, m in metrics_dict.items():
        doc.add_heading(f"File Analysis: {fname}", level=2)
        doc.add_heading("Time-Domain HRV Metrics", level=3)
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Metric'
        hdr_cells[1].text = 'Value'
        for k in ["Mean RR (ms)", "SDNN (ms)", "RMSSD (ms)", "Mean HR (bpm)", "NN50", "pNN50 (%)", "CV (%)"]:
            row_cells = table.add_row().cells
            row_cells[0].text = k
            row_cells[1].text = _safe(m.get(k))

        doc.add_heading("Frequency-Domain HRV Metrics", level=3)
        table_f = doc.add_table(rows=1, cols=2)
        table_f.style = 'Table Grid'
        hdr_cells = table_f.rows[0].cells
        hdr_cells[0].text = 'Metric'
        hdr_cells[1].text = 'Value'
        for k in ["VLF Power (ms2)", "LF Power (ms2)", "HF Power (ms2)", "LF/HF Ratio", "Total Power (ms2)", "LF norm (%)", "HF norm (%)"]:
            k_lookup = k.replace("2", "²") if k not in m else k
            row_cells = table_f.add_row().cells
            row_cells[0].text = k.replace("2", "²")
            row_cells[1].text = _safe(m.get(k_lookup))
            
        if "SD1 (ms)" in m:
            doc.add_heading("Non-Linear HRV Metrics", level=3)
            table_nl = doc.add_table(rows=1, cols=2)
            table_nl.style = 'Table Grid'
            hdr_cells = table_nl.rows[0].cells
            hdr_cells[0].text = 'Metric'
            hdr_cells[1].text = 'Value'
            for k in ["SD1 (ms)", "SD2 (ms)", "SD1/SD2", "Ellipse Area (ms2)", "Sample Entropy", "Approx Entropy", "DFA alpha1", "DFA alpha2"]:
                k_lookup = k.replace("alpha", "α").replace("2", "²") if k not in m else k
                row_cells = table_nl.add_row().cells
                row_cells[0].text = k.replace("alpha", "α").replace("2", "²")
                row_cells[1].text = _safe(m.get(k_lookup))

        doc.add_heading("Signal Visualizations", level=3)
        charts = _generate_report_charts(fname)
        chart_labels = {
            "ecg": "ECG Waveform (First 10s)", "rpeaks": "R-Peak Detection",
            "rr": "RR Interval Tachogram", "psd": "Power Spectral Density (Welch)",
            "poincare": "Poincaré Plot"
        }
        for ckey in ["ecg", "rpeaks", "rr", "psd", "poincare"]:
            if ckey in charts:
                doc.add_paragraph(chart_labels.get(ckey, ckey.upper()))
                img_stream = io.BytesIO(charts[ckey])
                doc.add_picture(img_stream, width=Inches(6.0))
                doc.add_paragraph()

    doc.add_heading("Discussion", level=1)
    for fname, m in metrics_dict.items():
        interp = interpret_hrv(m, m)
        doc.add_heading(f"Interpretation for {fname}", level=2)
        doc.add_paragraph(f"Overall HRV (SDNN): {interp.get('sdnn_class','N/A')}")
        doc.add_paragraph(f"Vagal Tone (RMSSD): {interp.get('autonomic','N/A')}")
        doc.add_paragraph(f"Sympathovagal Balance (LF/HF): {interp.get('lf_hf_class','N/A')}")
        a1 = m.get("DFA α1") or m.get("DFA alpha1")
        if a1 is not None:
            a1_interp = ("Uncorrelated (white noise)" if a1 < 0.5 else
                         "Healthy long-range correlations" if a1 < 1.0 else
                         "1/f (pink) noise" if a1 < 1.5 else
                         "Over-correlated (Brownian noise)")
            doc.add_paragraph(f"Fractal Scaling (DFA α1): {a1_interp}")

    doc.add_heading("HRV Physiology Background", level=1)
    doc.add_paragraph("Heart Rate Variability (HRV) reflects the variation in time between consecutive heartbeats.")
    doc.add_paragraph("• Low Frequency (LF): Reflects sympathetic and parasympathetic activity.")
    doc.add_paragraph("• High Frequency (HF): Primarily reflects parasympathetic (vagal) activity.")
    doc.add_paragraph("• LF/HF Ratio: Index of sympathovagal balance.")
    doc.add_paragraph("\nReport generated by Clinical Sentinel ECG & HRV Analysis Suite v2.0")

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
    with col1:
        st.download_button(label="📄 Download Report (.md)", data=report_md, file_name=f"HRV_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md", mime="text/markdown", use_container_width=True)

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
        st.download_button(label="📊 Download Metrics (.csv)", data=buf.getvalue(), file_name=f"HRV_Metrics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)

    with col3:
        methods_txt = (f"METHODS SUMMARY\n===============\n\nPipeline: ECG → Preprocessing → R-Peak → RR Intervals → Ectopic Correction → HRV Analysis\n\nFilter: {settings.get('lowcut')}–{settings.get('highcut')} Hz\nR-Peak: {settings.get('rpeak_method')}\n")
        st.download_button(label="📋 Download Methods (.txt)", data=methods_txt, file_name="HRV_Methods.txt", mime="text/plain", use_container_width=True)

    st.markdown("---")
    section_header("Clinical Interpretation Summary")
    for fname, m in metrics_dict.items():
        interp  = interpret_hrv(m, m)
        sqi     = sqi_cache.get(fname, {})
        lf_hf   = m.get("LF/HF Ratio", float('nan'))
        sqi_lbl = sqi.get("quality_label", "—") if sqi else "—"
        st.markdown(f"""
        <div style="background:#1a1c1f;border:1px solid #1e2023;border-left:4px solid #c3f400;border-radius:0.375rem;padding:1rem;margin-bottom:0.75rem;">
          <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
            <span style="font-weight:800;color:#849396;">{fname}</span>
            <span style="background:#c3f400;color:#000;font-size:0.6rem;padding:0.15rem 0.5rem;border-radius:0.2rem;">SQI: {sqi_lbl}</span>
          </div>
          <div style="font-size:0.8rem;color:#bac9cc;">
            <strong>HRV Status:</strong> {interp.get('sdnn_class','—')}<br>
            <strong>Vagal Tone:</strong> {interp.get('autonomic','—')}<br>
            <strong>Sympathovagal (LF/HF={lf_hf:.2f}):</strong> {interp.get('lf_hf_class','—')}
          </div>
        </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
