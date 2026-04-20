import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.sidebar_settings import render_sidebar_settings
from utils.hrv_analysis import get_nonlinear_hrv

st.set_page_config(page_title="Non-Linear HRV", page_icon="🔬", layout="wide")

def main():
    render_sidebar_settings()
    
    st.title("🔬 Dashboard 8: Non-Linear HRV & Poincaré")
    
    if "clean_rr_intervals" not in st.session_state or st.session_state.get("active_file") not in st.session_state.get("clean_rr_intervals", {}):
        st.warning("Please process RR intervals in Dashboard 4/5 first.")
        return
        
    active_file = st.session_state["active_file"]
    clean_rr = st.session_state["clean_rr_intervals"][active_file]
    
    st.markdown(f"### Poincare Plot for **{active_file}**")
    
    if len(clean_rr) < 2:
        st.error("Not enough data points.")
        return
        
    metrics = get_nonlinear_hrv(clean_rr)
    
    # Store metrics
    if "metrics" not in st.session_state:
        st.session_state["metrics"] = {}
    if active_file not in st.session_state["metrics"]:
        st.session_state["metrics"][active_file] = {}
    st.session_state["metrics"][active_file].update(metrics)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Metrics")
        st.metric("SD1 (Short-term)", f"{metrics['SD1 (ms)']:.2f} ms")
        st.metric("SD2 (Long-term)", f"{metrics['SD2 (ms)']:.2f} ms")
        st.metric("SD1/SD2 Ratio", f"{metrics['SD1/SD2']:.3f}")
        
        st.info("""
        **Interpretation Protocol:**
        - **SD1**: Standard deviation of the points perpendicular to the line of identity. Corresponds to short-term variability (Parasympathetic).
        - **SD2**: Standard deviation along the line of identity. Represents long-term variability.
        """)
        
    with col2:
        rr_n = clean_rr[:-1]
        rr_n1 = clean_rr[1:]
        
        fig = go.Figure()
        
        # Scatter points
        fig.add_trace(go.Scatter(
            x=rr_n, y=rr_n1, mode='markers',
            marker=dict(color='rgba(135, 206, 250, 0.6)', size=6, line=dict(color='white', width=0.5)),
            name='RR pairs'
        ))
        
        # Line of identity
        min_val = min(np.min(rr_n), np.min(rr_n1))
        max_val = max(np.max(rr_n), np.max(rr_n1))
        fig.add_trace(go.Scatter(
            x=[min_val, max_val], y=[min_val, max_val],
            mode='lines', line=dict(color='gray', dash='dash'),
            name='Identity Line'
        ))
        
        # Ellipse overlay (simplified bounds for visualization)
        # Using parametric ellipse equation on rotated axes
        mean_rr = np.mean(clean_rr)
        theta = np.linspace(0, 2*np.pi, 100)
        
        # The axes are rotated by 45 degrees (pi/4)
        rot_angle = np.pi / 4
        # Semi-major (SD2) and semi-minor (SD1)
        a = metrics['SD2 (ms)']
        b = metrics['SD1 (ms)']
        
        x_ell = mean_rr + a * np.cos(theta) * np.cos(rot_angle) - b * np.sin(theta) * np.sin(rot_angle)
        y_ell = mean_rr + a * np.cos(theta) * np.sin(rot_angle) + b * np.sin(theta) * np.cos(rot_angle)
        
        fig.add_trace(go.Scatter(
            x=x_ell, y=y_ell, mode='lines', line=dict(color='#ff0066', width=2), name='SD1/SD2 Ellipse'
        ))
        
        theme = st.session_state.get("plot_theme", "plotly_dark")
        fig.update_layout(
            title="Poincaré Plot: RR(n) vs RR(n+1)",
            xaxis_title="RR(n) (ms)",
            yaxis_title="RR(n+1) (ms)",
            template=theme,
            width=600, height=500
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
