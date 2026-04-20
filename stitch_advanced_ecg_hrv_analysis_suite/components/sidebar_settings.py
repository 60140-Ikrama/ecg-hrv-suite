"""
Sidebar Settings (Dashboard 9): Central settings panel shared across all pages.
Reads/writes to st.session_state so all dashboards react to changes.
"""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _default(key, val):
    if key not in st.session_state:
        st.session_state[key] = val


def render_sidebar_settings():
    """
    Renders the unified settings sidebar. Must be called at the top of each page.
    """
    # ── Defaults ──────────────────────────────────────────────────────────────
    _default("sfreq", 250.0)
    _default("auto_sfreq", False)
    _default("lowcut", 0.5)
    _default("highcut", 40.0)
    _default("remove_baseline", True)
    _default("noise_method", "None")
    _default("rpeak_method", "NeuroKit")
    _default("remove_ectopic", True)
    _default("ectopic_threshold", 20)
    _default("ectopic_interp", "Linear")
    _default("lf_min", 0.04)
    _default("lf_max", 0.15)
    _default("hf_min", 0.15)
    _default("hf_max", 0.40)
    _default("plot_theme", "plotly_dark")

    with st.sidebar:
        st.markdown("""
        <div style="padding:0.75rem 0 0.5rem;font-family:'Manrope',sans-serif;
                    font-size:0.6rem;font-weight:800;color:#849396;
                    text-transform:uppercase;letter-spacing:0.15em;border-bottom:1px solid #1e2023;
                    margin-bottom:0.75rem;">
        ⚙️ Pipeline Settings
        </div>
        """, unsafe_allow_html=True)

        # ── Signal Settings ────────────────────────────────────────────────────
        with st.expander("📡 Signal", expanded=True):
            st.session_state["auto_sfreq"] = st.checkbox(
                "Auto-detect Fs", value=st.session_state["auto_sfreq"])
            if not st.session_state["auto_sfreq"]:
                st.session_state["sfreq"] = st.number_input(
                    "Sampling Frequency (Hz)",
                    value=float(st.session_state["sfreq"]),
                    min_value=1.0, max_value=5000.0, step=50.0)

        # ── Filter Settings ───────────────────────────────────────────────────
        with st.expander("🧹 Filter"):
            st.session_state["remove_baseline"] = st.checkbox(
                "Remove Baseline Wander", value=st.session_state["remove_baseline"])
            c1, c2 = st.columns(2)
            with c1:
                st.session_state["lowcut"] = st.number_input(
                    "Low (Hz)", value=float(st.session_state["lowcut"]),
                    min_value=0.01, max_value=5.0, step=0.1)
            with c2:
                st.session_state["highcut"] = st.number_input(
                    "High (Hz)", value=float(st.session_state["highcut"]),
                    min_value=5.0, max_value=500.0, step=5.0)
            st.session_state["noise_method"] = st.selectbox(
                "Extra Filter",
                ["None", "Wavelet", "Powerline 50Hz", "Powerline 60Hz"],
                index=["None", "Wavelet", "Powerline 50Hz", "Powerline 60Hz"].index(
                    st.session_state["noise_method"]))

        # ── R-Peak Settings ───────────────────────────────────────────────────
        with st.expander("❤️ R-Peak"):
            methods = ["NeuroKit", "Pan-Tompkins", "Hamilton", "Elgendi", "Rodrigues"]
            st.session_state["rpeak_method"] = st.selectbox(
                "Algorithm", methods,
                index=methods.index(st.session_state["rpeak_method"]) if st.session_state["rpeak_method"] in methods else 0)

        # ── Ectopic Settings ──────────────────────────────────────────────────
        with st.expander("⚠️ Ectopic"):
            st.session_state["remove_ectopic"] = st.checkbox(
                "Enable Correction", value=st.session_state["remove_ectopic"])
            st.session_state["ectopic_threshold"] = st.slider(
                "Outlier Threshold (%)", 5, 50,
                value=st.session_state["ectopic_threshold"], step=5)
            st.session_state["ectopic_interp"] = st.selectbox(
                "Interpolation", ["Linear", "Spline"],
                index=["Linear", "Spline"].index(st.session_state["ectopic_interp"]))

        # ── HRV Settings ──────────────────────────────────────────────────────
        with st.expander("📈 HRV Bands"):
            c1, c2 = st.columns(2)
            with c1:
                st.session_state["lf_min"] = st.number_input(
                    "LF min (Hz)", value=float(st.session_state["lf_min"]),
                    min_value=0.01, step=0.01)
                st.session_state["lf_max"] = st.number_input(
                    "LF max (Hz)", value=float(st.session_state["lf_max"]),
                    min_value=0.05, step=0.01)
            with c2:
                st.session_state["hf_min"] = st.number_input(
                    "HF min (Hz)", value=float(st.session_state["hf_min"]),
                    min_value=0.05, step=0.01)
                st.session_state["hf_max"] = st.number_input(
                    "HF max (Hz)", value=float(st.session_state["hf_max"]),
                    min_value=0.10, step=0.01)

        # ── UI Settings ───────────────────────────────────────────────────────
        st.markdown("---")
        theme_choice = st.selectbox("📊 Plot Theme", ["Dark (Clinical)", "Light"])
        st.session_state["plot_theme"] = "plotly_dark" if "Dark" in theme_choice else "plotly_white"

        st.markdown(
            '<div style="font-size:0.6rem;color:#3b494c;font-family:Inter;margin-top:1rem;text-align:center;">'
            'Changes propagate to all dashboards.</div>',
            unsafe_allow_html=True
        )
