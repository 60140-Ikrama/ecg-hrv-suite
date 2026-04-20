import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="Multi-File Comparison", page_icon="📁", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("📁 Dashboard 10: Multi-File Comparison")
    st.markdown("Compare HRV parameters across all analyzed subjects/files.")
    
    if "metrics" not in st.session_state or len(st.session_state["metrics"]) < 1:
        st.warning("No metrics found. Please process at least one file entirely to perform comparisons.")
        return
        
    metrics_dict = st.session_state["metrics"]
    
    # Check what files are fully analyzed to prevent KeyError
    analyzed_files = []
    for f in metrics_dict:
        # A fully analyzed file has Time, Freq, and Nonlinear metrics
        if "SDNN (ms)" in metrics_dict[f] and "LF/HF Ratio" in metrics_dict[f] and "SD1 (ms)" in metrics_dict[f]:
            analyzed_files.append(f)
            
    if not analyzed_files:
        st.warning("Some files are only partially processed. Please ensure you view Dashboards 6, 7, and 8 for the files you wish to compare.")
        return
        
    st.success(f"Comparing {len(analyzed_files)} processed files.")
    
    data = []
    for f in analyzed_files:
        row = {"File Name": f}
        row.update({k: v for k, v in metrics_dict[f].items()})
        data.append(row)
        
    df = pd.DataFrame(data)
    
    st.subheader("Statistical Summary Table")
    st.dataframe(df.style.format(precision=3), use_container_width=True)
    
    # Graphs
    theme = st.session_state.get("plot_theme", "plotly_dark")
    st.subheader("Visual Comparisons")
    
    col1, col2, col3 = st.columns(3)
    
    # Graph 1: SDNN
    with col1:
        fig1 = go.Figure([go.Bar(x=df["File Name"], y=df["SDNN (ms)"], marker_color='#1f77b4')])
        fig1.update_layout(title="SDNN Comparison", template=theme, yaxis_title="ms")
        st.plotly_chart(fig1, use_container_width=True)
        
    # Graph 2: LF/HF Ratio
    with col2:
        fig2 = go.Figure([go.Bar(x=df["File Name"], y=df["LF/HF Ratio"], marker_color='#ff7f0e')])
        fig2.update_layout(title="LF/HF Ratio", template=theme, yaxis_title="Ratio")
        st.plotly_chart(fig2, use_container_width=True)
        
    # Graph 3: Scatter Time vs Freq
    with col3:
        fig3 = go.Figure(data=go.Scatter(
            x=df["RMSSD (ms)"],
            y=df["HF Power"],
            mode='markers+text',
            text=df["File Name"],
            textposition="top center",
            marker=dict(size=12, color=df["SD1 (ms)"], colorscale='Viridis', showscale=True)
        ))
        fig3.update_layout(title="RMSSD vs HF Power", xaxis_title="RMSSD (ms)", yaxis_title="HF Power", template=theme)
        st.plotly_chart(fig3, use_container_width=True)

if __name__ == "__main__":
    main()
