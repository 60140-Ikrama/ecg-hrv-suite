import streamlit as st
import pandas as pd
import json
import io
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="Report Generation", page_icon="📑", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("📑 Report Generation (CLO3)")
    st.markdown("Generate and download comprehensive analysis reports.")
    
    if "metrics" not in st.session_state or len(st.session_state["metrics"]) < 1:
        st.warning("No metrics computed yet. Complete the analysis pipeline first.")
        return
        
    metrics_dict = st.session_state["metrics"]
    df = pd.DataFrame.from_dict(metrics_dict, orient='index')
    df.index.name = "File Name"
    df.reset_index(inplace=True)
    
    st.write(f"Available data for {len(df)} file(s).")
    
    # Text summary strategy mapping
    def interpret_lfhf(val):
        if pd.isna(val): return "Inconclusive"
        if val > 2.0: return "Sympathetic dominance (Stress/Activity)"
        elif val < 1.0: return "Parasympathetic dominance (Relaxation)"
        else: return "Balanced tone"
        
    df["Autonomic Balance Interpretation"] = df.get("LF/HF Ratio", pd.Series([float('nan')]*len(df))).apply(interpret_lfhf)
    
    # Generate Markdown Report
    report_md = f"# ECG & HRV Professional Analysis Report\n\n"
    report_md += f"**Date Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_md += f"## 1. Methodology\n"
    report_md += f"Analysis was performed using the advanced pipeline:\n"
    report_md += f"- **Filtering:** {st.session_state.get('lowcut', 0.5)}-{st.session_state.get('highcut', 40.0)} Hz Bandpass, Baseline Wander Removal: {st.session_state.get('baseline_wander', True)}\n"
    report_md += f"- **R-Peak Algorithm:** {st.session_state.get('rpeak_method', 'NeuroKit')}\n"
    report_md += f"- **Ectopic Correction:** {st.session_state.get('remove_ectopic', True)} (Threshold: {st.session_state.get('ectopic_threshold', 0.2)}, Method: {st.session_state.get('ectopic_interp', 'Linear')})\n\n"
    
    report_md += f"## 2. Results Summary\n\n"
    report_md += df.to_markdown(index=False)
    
    report_md += f"\n\n## 3. Clinical Interpretations\n\n"
    for idx, row in df.iterrows():
        report_md += f"### File: {row['File Name']}\n"
        report_md += f"- **Sympathetic vs Parasympathetic Balance:** Based on an LF/HF ratio of {row.get('LF/HF Ratio', 'N/A'):.2f}, this subject exhibits *{row.get('Autonomic Balance Interpretation', 'N/A')}*.\n"
        report_md += f"- **Overall HRV (SDNN):** {row.get('SDNN (ms)', 'N/A'):.1f} ms.\n\n"
        
    st.markdown("### Preview Report")
    st.markdown(report_md)
    
    # Download Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download Report as Markdown (.md)",
            data=report_md,
            file_name="HRV_Analysis_Report.md",
            mime="text/markdown"
        )
        
    with col2:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📊 Download Metrics as CSV",
            data=csv_buffer.getvalue(),
            file_name="HRV_Metrics_Summary.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
