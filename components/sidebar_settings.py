"""
Sidebar Settings (Dashboard 9): Unified control panel — reads/writes
st.session_state so every dashboard reacts to changes live.
"""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _default(key, val):
    if key not in st.session_state:
        st.session_state[key] = val


def _sb_label(icon: str, text: str, color: str = "#3b494c"):
    """Render a styled sidebar section label."""
    st.markdown(
        f'<div class="sb-section-lbl" style="color:{color};">'
        f'<span>{icon}</span>{text}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_settings():
    """Render the unified settings sidebar. Call at the top of every page."""

    # ── Defaults ──────────────────────────────────────────────────────────────
    _default("sfreq",             250.0)
    _default("auto_sfreq",        False)
    _default("lowcut",            0.5)
    _default("highcut",           40.0)
    _default("remove_baseline",   True)
    _default("noise_method",      "None")
    _default("filter_order",      4)
    _default("rpeak_method",      "NeuroKit")
    _default("remove_ectopic",    True)
    _default("ectopic_threshold", 20)
    _default("ectopic_method",    "median")
    _default("ectopic_interp",    "Linear")
    _default("lf_min",            0.04)
    _default("lf_max",            0.15)
    _default("hf_min",            0.15)
    _default("hf_max",            0.40)
    _default("welch_nperseg",     256)
    _default("welch_noverlap",    128)
    _default("enable_dfa",        True)
    _default("anomaly_z",         3.0)
    _default("sqi_threshold",     35.0)
    _default("plot_theme",        "plotly_dark")

    with st.sidebar:

        # ── Branded Header ─────────────────────────────────────────────────
        st.markdown("""
        <div class="sb-brand">
          <span class="sb-brand-icon">&#x1FAC0;</span>
          <div>
            <div class="sb-brand-name">Clinical Sentinel</div>
            <div class="sb-brand-sub">ECG &amp; HRV Analysis Suite</div>
          </div>
          <span class="sb-ver">v2.0</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Signal ────────────────────────────────────────────────────────────
        _sb_label("📡", "Signal Input", "#00daf3")
        with st.expander("Signal Settings", expanded=True):
            st.session_state["auto_sfreq"] = st.checkbox(
                "Auto-detect Fs", value=st.session_state["auto_sfreq"])
            if not st.session_state["auto_sfreq"]:
                st.session_state["sfreq"] = st.number_input(
                    "Sampling Frequency (Hz)",
                    value=float(st.session_state["sfreq"]),
                    min_value=1.0, max_value=5000.0, step=50.0)
            st.session_state["sqi_threshold"] = st.slider(
                "Min SQI (reject below)", 0, 80,
                value=int(st.session_state["sqi_threshold"]), step=5)

        # ── Filter ────────────────────────────────────────────────────────────
        _sb_label("🧹", "Filter Chain")
        with st.expander("Filter Settings"):
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
            st.session_state["filter_order"] = st.selectbox(
                "Filter Order", [2, 3, 4, 5],
                index=[2, 3, 4, 5].index(st.session_state["filter_order"]))
            st.session_state["noise_method"] = st.selectbox(
                "Extra Filter",
                ["None", "Wavelet", "Powerline 50Hz", "Powerline 60Hz", "Adaptive"],
                index=["None", "Wavelet", "Powerline 50Hz", "Powerline 60Hz", "Adaptive"]
                      .index(st.session_state["noise_method"]))

        # ── R-Peak ────────────────────────────────────────────────────────────
        _sb_label("❤️", "R-Peak Detection", "#c3f400")
        with st.expander("Algorithm"):
            methods = ["NeuroKit", "Pan-Tompkins (Custom)",
                       "Pan-Tompkins", "Hamilton", "Elgendi", "Rodrigues"]
            cur = st.session_state["rpeak_method"]
            st.session_state["rpeak_method"] = st.selectbox(
                "Algorithm", methods,
                index=methods.index(cur) if cur in methods else 0)

        # ── Ectopic ───────────────────────────────────────────────────────────
        _sb_label("⚠️", "Ectopic Beats", "#ffba38")
        with st.expander("Ectopic Settings"):
            st.session_state["remove_ectopic"] = st.checkbox(
                "Enable Correction", value=st.session_state["remove_ectopic"])
            st.session_state["ectopic_method"] = st.selectbox(
                "Detection Method",
                ["median", "mean", "combined"],
                index=["median", "mean", "combined"]
                      .index(st.session_state["ectopic_method"]))
            st.session_state["ectopic_threshold"] = st.slider(
                "Outlier Threshold (%)", 5, 50,
                value=st.session_state["ectopic_threshold"], step=5)
            st.session_state["ectopic_interp"] = st.selectbox(
                "Interpolation", ["Linear", "Spline"],
                index=["Linear", "Spline"].index(st.session_state["ectopic_interp"]))
            st.session_state["anomaly_z"] = st.slider(
                "Anomaly Z-score", 1.5, 5.0,
                value=float(st.session_state["anomaly_z"]), step=0.5)

        # ── HRV Bands ─────────────────────────────────────────────────────────
        _sb_label("📈", "HRV Bands", "#c3f400")
        with st.expander("Frequency Bands"):
            c1, c2 = st.columns(2)
            with c1:
                st.session_state["lf_min"] = st.number_input(
                    "LF min", value=float(st.session_state["lf_min"]),
                    min_value=0.01, step=0.01)
                st.session_state["lf_max"] = st.number_input(
                    "LF max", value=float(st.session_state["lf_max"]),
                    min_value=0.05, step=0.01)
            with c2:
                st.session_state["hf_min"] = st.number_input(
                    "HF min", value=float(st.session_state["hf_min"]),
                    min_value=0.05, step=0.01)
                st.session_state["hf_max"] = st.number_input(
                    "HF max", value=float(st.session_state["hf_max"]),
                    min_value=0.10, step=0.01)

        # ── Welch PSD ─────────────────────────────────────────────────────────
        _sb_label("📊", "Welch PSD")
        with st.expander("PSD Settings"):
            st.session_state["welch_nperseg"] = st.selectbox(
                "nperseg (window)", [64, 128, 256, 512],
                index=[64, 128, 256, 512].index(st.session_state["welch_nperseg"]))
            max_ov = st.session_state["welch_nperseg"] - 1
            st.session_state["welch_noverlap"] = st.slider(
                "noverlap", 0, max_ov,
                value=min(st.session_state["welch_noverlap"], max_ov), step=32)

        # ── Advanced ──────────────────────────────────────────────────────────
        _sb_label("🔬", "Advanced")
        with st.expander("Advanced Options"):
            st.session_state["enable_dfa"] = st.checkbox(
                "Compute DFA (α1 / α2)", value=st.session_state["enable_dfa"])

        # ── Theme Engine ──────────────────────────────────────────────────────
        st.markdown(
            '<div style="height:1px;background:linear-gradient(90deg,#1e2023,#282a2d,#1e2023);margin:0.75rem 0;"></div>',
            unsafe_allow_html=True)

        _sb_label("🎨", "App Theme")
        PRESET_THEMES = {
            "Clinical Sentinel (Dark)": None,
            "Light Mode": {
                "surface_container_lowest": "#f0f2f5",
                "surface_container_low":    "#ffffff",
                "surface_container":        "#e4e7eb",
                "surface_container_high":   "#d1d5db",
                "on_surface":               "#111827",
                "on_surface_variant":       "#374151",
                "primary":                  "#0ea5e9",
                "primary_dim":              "#0284c7",
                "outline":                  "#9ca3af",
                "outline_variant":          "#cbd5e1",
                "secondary_fixed":          "#10b981",
                "tertiary_fixed_dim":       "#f59e0b",
                "surface":                  "#ffffff",
            },
            "Neon Cyberpunk": {
                "surface_container_lowest": "#050014",
                "surface_container_low":    "#0a0026",
                "surface_container":        "#110038",
                "surface_container_high":   "#1a004a",
                "on_surface":               "#ff00ff",
                "on_surface_variant":       "#00ffff",
                "primary":                  "#00ffff",
                "primary_dim":              "#00b3b3",
                "secondary_fixed":          "#ff00ff",
                "outline":                  "#39ff14",
                "outline_variant":          "#39ff14",
                "tertiary_fixed_dim":       "#ffff00",
                "surface":                  "#050014",
            },
        }

        # Colour swatches preview
        SWATCH_COLORS = {
            "Clinical Sentinel (Dark)": ["#00daf3","#c3f400","#ffba38","#111316"],
            "Light Mode":               ["#0ea5e9","#10b981","#f59e0b","#f0f2f5"],
            "Neon Cyberpunk":           ["#00ffff","#ff00ff","#39ff14","#050014"],
        }
        swatch_html = '<div style="display:flex;gap:0.6rem;margin:0.4rem 0 0.65rem;">'
        for name, colors in SWATCH_COLORS.items():
            dots = "".join(
                f'<span style="width:10px;height:10px;border-radius:50%;'
                f'background:{c};display:inline-block;border:1px solid rgba(255,255,255,0.1);"></span>'
                for c in colors
            )
            swatch_html += (
                f'<div style="display:flex;align-items:center;gap:2px;" title="{name}">{dots}</div>'
            )
        swatch_html += '</div>'
        st.markdown(swatch_html, unsafe_allow_html=True)

        with st.expander("Theme Presets"):
            sel_theme = st.selectbox("Select Preset", list(PRESET_THEMES.keys()),
                                     label_visibility="collapsed")

            if PRESET_THEMES[sel_theme] is not None:
                st.session_state["active_theme_dict"] = PRESET_THEMES[sel_theme]
                st.session_state["plot_theme"] = (
                    "plotly_white" if "Light" in sel_theme else "plotly_dark")
            else:
                if "active_theme_dict" in st.session_state and \
                        not st.session_state.get("custom_theme_active"):
                    del st.session_state["active_theme_dict"]
                st.session_state["plot_theme"] = "plotly_dark"

            st.markdown(
                '<div style="font-size:0.68rem;color:#849396;margin:0.6rem 0 0.2rem;">'
                'Import from JSON URL</div>',
                unsafe_allow_html=True)
            theme_url = st.text_input("Theme URL", placeholder="https://.../theme.json",
                                      label_visibility="collapsed")
            if st.button("Fetch Custom Theme", use_container_width=True) and theme_url:
                import requests
                try:
                    resp = requests.get(theme_url, timeout=5)
                    resp.raise_for_status()
                    custom_colors = resp.json()
                    if isinstance(custom_colors, dict):
                        st.session_state["active_theme_dict"] = custom_colors
                        st.session_state["custom_theme_active"] = True
                        st.success("Theme Applied!")
                        st.rerun()
                except Exception:
                    st.error("Failed to load JSON")

        # ── Live Sync Indicator ───────────────────────────────────────────────
        st.markdown("""
        <div class="sb-sync-pill">
          <span class="dot"></span>
          Live sync &nbsp;·&nbsp; All dashboards update instantly
        </div>
        """, unsafe_allow_html=True)
