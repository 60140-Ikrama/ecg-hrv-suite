import streamlit as st

def render_sidebar_settings():
    """
    Renders the unified settings sidebar across all pages.
    Updates st.session_state dynamically.
    """
    st.sidebar.title("⚙️ System Settings")
    st.sidebar.markdown("---")
    
    # Defaults in session_state
    if "sfreq" not in st.session_state:
        st.session_state["sfreq"] = 250.0  # default 250Hz but allow update

    # --- 1. Signal Settings ---
    with st.sidebar.expander("📡 Signal Settings", expanded=True):
        st.session_state["auto_sfreq"] = st.checkbox("Auto-detect Sampling Freq", value=False)
        st.session_state["sfreq"] = st.number_input(
            "Manual Sampling Freq (Hz)", 
            value=st.session_state["sfreq"], 
            min_value=1.0, 
            step=10.0,
            disabled=st.session_state["auto_sfreq"]
        )

    # --- 2. Filter Settings ---
    with st.sidebar.expander("🧹 Filter Settings"):
        st.session_state["baseline_wander"] = st.checkbox("Remove Baseline Wander", value=True)
        st.session_state["lowcut"] = st.number_input("Bandpass Low Cutoff (Hz)", value=0.5, step=0.1)
        st.session_state["highcut"] = st.number_input("Bandpass High Cutoff (Hz)", value=40.0, step=1.0)
        st.session_state["noise_method"] = st.selectbox("Additional Noise Filter", ["None", "Wavelet", "Powerline Removal (50/60 Hz)"])

    # --- 3. R-Peak Settings ---
    with st.sidebar.expander("❤️ R-Peak Settings"):
        st.session_state["rpeak_method"] = st.selectbox("Detection Method", ["NeuroKit", "Pan-Tompkins", "Hamilton"])

    # --- 4. Ectopic Settings ---
    with st.sidebar.expander("⚠️ Ectopic Beat Settings"):
        st.session_state["remove_ectopic"] = st.checkbox("Enable Correction", value=True)
        st.session_state["ectopic_threshold"] = st.slider("Outlier Threshold (%)", min_value=10, max_value=50, value=20, step=5) / 100.0
        st.session_state["ectopic_interp"] = st.selectbox("Correction Method", ["Linear", "Spline"])

    # --- 5. HRV Settings ---
    with st.sidebar.expander("📈 HRV Settings"):
        st.write("PSD Frequency Bands")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["lf_min"] = st.number_input("LF Min (Hz)", value=0.04, step=0.01)
            st.session_state["lf_max"] = st.number_input("LF Max (Hz)", value=0.15, step=0.01)
        with col2:
            st.session_state["hf_min"] = st.number_input("HF Min (Hz)", value=0.15, step=0.01)
            st.session_state["hf_max"] = st.number_input("HF Max (Hz)", value=0.40, step=0.01)

    # --- 6. UI Settings ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("🎨 **UI Theme**")
    theme = st.sidebar.radio("Plot Theme", ["Plotly Dark", "Plotly White"])
    st.session_state["plot_theme"] = "plotly_dark" if theme == "Plotly Dark" else "plotly_white"
    
    st.sidebar.markdown("---")
    st.sidebar.info("Tip: Settings update automatically and propagate to all dashboards.")
