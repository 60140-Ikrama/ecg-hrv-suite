"""
Stitch Design System: CSS injection and shared UI components.
Applies Clinical Sentinel theme tokens to Streamlit.
"""
import copy
import streamlit as st

# === STITCH DESIGN TOKENS ===
DEFAULT_COLORS = {
    "primary": "#c3f5ff",
    "primary_dim": "#00daf3",
    "secondary_fixed": "#c3f400",
    "secondary_fixed_dim": "#abd600",
    "tertiary_fixed_dim": "#ffba38",
    "surface": "#111316",
    "surface_container_lowest": "#0c0e11",
    "surface_container_low": "#1a1c1f",
    "surface_container": "#1e2023",
    "surface_container_high": "#282a2d",
    "surface_container_highest": "#333538",
    "on_surface": "#e2e2e6",
    "on_surface_variant": "#bac9cc",
    "outline": "#849396",
    "outline_variant": "#3b494c",
    "on_primary": "#00363d",
    "error": "#ffb4ab",
    "error_container": "#93000a",
    "on_error": "#690005"
}

class DynamicColors(dict):
    """Lazily fetches colors from st.session_state so the UI can be themed dynamically."""
    def __getitem__(self, key):
        import streamlit as st
        theme = st.session_state.get("active_theme_dict", DEFAULT_COLORS)
        return theme.get(key, DEFAULT_COLORS.get(key, "#ffffff"))
        
    def get(self, key, default=None):
        import streamlit as st
        theme = st.session_state.get("active_theme_dict", DEFAULT_COLORS)
        return theme.get(key, DEFAULT_COLORS.get(key, default))

COLORS = DynamicColors(DEFAULT_COLORS)

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["surface_container_lowest"],
    plot_bgcolor=COLORS["surface_container_lowest"],
    font=dict(family="Inter, sans-serif", color=COLORS["on_surface_variant"], size=11),
    # Removed default title key to prevent "multiple values for keyword argument 'title'" errors
    margin=dict(l=50, r=20, t=50, b=50),
    xaxis=dict(
        gridcolor=COLORS["outline_variant"],
        linecolor=COLORS["outline_variant"],
        tickfont=dict(color=COLORS["on_surface_variant"]),
        title_font=dict(color=COLORS["on_surface_variant"]),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor=COLORS["outline_variant"],
        linecolor=COLORS["outline_variant"],
        tickfont=dict(color=COLORS["on_surface_variant"]),
        title_font=dict(color=COLORS["on_surface_variant"]),
        zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(17,19,22,0.8)",
        bordercolor=COLORS["outline_variant"],
        borderwidth=1,
        font=dict(color=COLORS["on_surface_variant"])
    ),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor=COLORS["surface_container_high"],
        bordercolor=COLORS["outline_variant"],
        font=dict(color=COLORS["on_surface"], family="Inter"),
    ),
    annotationdefaults=dict(
        font=dict(family="Manrope, sans-serif", color=COLORS["on_surface_variant"], size=11),
        showarrow=False,
    ),
)

STITCH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* Core Reset */
html, body, [class*="css"], .stApp { 
    font-family: 'Inter', sans-serif !important;
    background-color: #111316 !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer { display: none !important; }
.stDeployButton { display: none !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

/* Premium Sidebar Unhide/Hide Toggle Button */
div[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"] {
    background: rgba(17, 19, 22, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(0, 218, 243, 0.4) !important;
    border-radius: 50% !important;
    color: #00daf3 !important;
    box-shadow: 0 4px 12px rgba(0, 218, 243, 0.15), inset 0 0 0 1px rgba(255,255,255,0.05) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin-left: 1rem !important;
    margin-top: 0.8rem !important;
    width: 42px !important;
    height: 42px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 9999999 !important;
    visibility: visible !important;
    opacity: 1 !important;
}
div[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover,
button[kind="header"]:hover {
    background: rgba(0, 218, 243, 0.15) !important;
    border-color: #00daf3 !important;
    box-shadow: 0 6px 16px rgba(0, 218, 243, 0.3), inset 0 0 0 1px rgba(255,255,255,0.1) !important;
    transform: scale(1.1) !important;
}
div[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
button[kind="header"] svg {
    fill: #00daf3 !important;
    width: 20px !important;
    height: 20px !important;
    transition: fill 0.3s ease !important;
}
div[data-testid="stSidebarCollapsedControl"]:hover svg,
[data-testid="collapsedControl"]:hover svg,
button[kind="header"]:hover svg {
    fill: #c3f5ff !important;
}

/* Force header visibility for the button container */
header {
    visibility: visible !important;
    background: transparent !important;
    z-index: 9999998 !important;
}

/* Page title banner */
.sentinel-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background: #111316;
    border-bottom: 1px solid #1e2023;
    margin-bottom: 1.5rem;
    border-radius: 0 0 0.5rem 0.5rem;
}
.sentinel-header h1 {
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800;
    font-size: 1.2rem;
    color: #c3f5ff;
    text-transform: uppercase;
    letter-spacing: -0.03em;
    margin: 0;
}
.sentinel-badge {
    font-family: 'Manrope', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    color: #161e00;
    background: #c3f400;
    padding: 0.15rem 0.5rem;
    border-radius: 0.2rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* KPI Cards */
.kpi-card {
    background: #1a1c1f;
    border: 1px solid #1e2023;
    border-radius: 0.375rem;
    padding: 1rem 1.25rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: #3b494c; }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: #00daf3;
    border-radius: 0 2px 2px 0;
}
.kpi-card.accent-green::before { background: #c3f400; }
.kpi-card.accent-amber::before { background: #ffba38; }
.kpi-card.accent-red::before { background: #ffb4ab; }
.kpi-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    color: #bac9cc;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.35rem;
}
.kpi-value {
    font-family: 'Manrope', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #c3f5ff;
    line-height: 1;
}
.kpi-value.green { color: #c3f400; }
.kpi-value.amber { color: #ffba38; }
.kpi-unit {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #849396;
    margin-left: 0.2rem;
}
.kpi-bar {
    height: 3px;
    background: #282a2d;
    border-radius: 2px;
    margin-top: 0.75rem;
    overflow: hidden;
}
.kpi-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: #00daf3;
    box-shadow: 0 0 8px rgba(0,218,243,0.4);
}

/* Section Headers */
.section-header {
    font-family: 'Manrope', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    color: #849396;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e2023;
}

/* Glass Panel */
.glass-panel {
    background: rgba(51, 53, 56, 0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(59, 73, 76, 0.4);
    border-radius: 0.375rem;
    padding: 1rem 1.25rem;
}

/* Clinical Interpretation Box */
.clinical-card {
    background: #1a1c1f;
    border-left: 4px solid #00daf3;
    border-radius: 0 0.375rem 0.375rem 0;
    padding: 1rem 1.25rem;
}
.clinical-card.warning { border-left-color: #ffba38; }
.clinical-card.success { border-left-color: #c3f400; }
.clinical-title {
    font-family: 'Manrope', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    color: #00daf3;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.clinical-body {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #bac9cc;
    line-height: 1.6;
}

/* Pipeline steps */
.pipeline-step {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #1e2023;
    border: 1px solid #3b494c;
    border-radius: 0.25rem;
    padding: 0.3rem 0.6rem;
    font-family: 'Manrope', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    color: #bac9cc;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.pipeline-step.active {
    background: rgba(0, 218, 243, 0.1);
    border-color: #00daf3;
    color: #c3f5ff;
    box-shadow: 0 0 12px rgba(0, 218, 243, 0.15);
}
.pipeline-arrow { color: #3b494c; font-size: 1rem; }

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0c0e11 !important;
    border-right: 1px solid #1e2023;
}
/* Ensure Material Symbols render correctly — do NOT override their font */
.material-symbols-rounded,
.material-symbols-outlined,
[class*="material-symbols"],
section[data-testid="stSidebar"] span[class*="material"] { 
    font-family: "Material Symbols Rounded" !important; 
}

/* Base font for sidebar text (avoids global span overrides that break ligatures) */
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span:not([class*="material"]) { 
    font-family: 'Inter', sans-serif !important; 
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Manrope', sans-serif !important;
    color: #c3f5ff !important;
}

/* Streamlit widget overrides */
.stSelectbox label, .stSlider label, .stCheckbox label, 
.stNumberInput label, .stRadio label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    color: #bac9cc !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stExpander"] {
    background: #1a1c1f !important;
    border: 1px solid #1e2023 !important;
    border-radius: 0.375rem !important;
}
div[data-testid="stExpander"] summary {
    color: #c3f5ff !important;
    list-style: none !important;
}
/* Target only the text label inside the summary */
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary .st-emotion-cache-1104aqp {
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: #c3f5ff !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
/* Prevent SVG and Material arrows from inheriting font overrides */
div[data-testid="stExpander"] summary svg,
div[data-testid="stExpander"] summary span[class*="material"] {
    font-family: "Material Symbols Rounded" !important;
    display: inline-block !important;
    visibility: visible !important;
}
.stAlert { border-radius: 0.375rem !important; }

/* Tab styling */
button[data-baseweb="tab"] {
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #849396 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #c3f5ff !important;
    border-bottom-color: #00daf3 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #1a1c1f;
    border: 1px solid #1e2023;
    border-radius: 0.375rem;
    padding: 0.75rem;
}
[data-testid="stMetricLabel"] > div {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.6rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #849396 !important;
}
[data-testid="stMetricValue"] > div {
    font-family: 'Manrope', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #c3f5ff !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2023;
    border-radius: 0.375rem;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: #1a1c1f;
    border: 1px dashed #3b494c;
    border-radius: 0.375rem;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #00daf3; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0c0e11; }
::-webkit-scrollbar-thumb { background: #3b494c; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #849396; }

/* ── ANIMATIONS ─────────────────────────────────────────────────────────── */
@keyframes pulse-glow {
    0%,100% { filter: drop-shadow(0 0 6px rgba(0,218,243,0.5)); }
    50%      { filter: drop-shadow(0 0 18px rgba(0,218,243,1)); }
}
@keyframes ecg-draw {
    0%   { stroke-dashoffset: 800; opacity:0.3; }
    50%  { opacity: 1; }
    100% { stroke-dashoffset: 0; opacity:0.3; }
}
@keyframes fadeInUp {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes blink-dot {
    0%,100% { opacity:1; }
    50%      { opacity:0.25; }
}
@keyframes shimmer-bar {
    0%   { background-position: -400px 0; }
    100% { background-position:  400px 0; }
}

/* ── HERO SECTION ──────────────────────────────────────────────────────── */
.hero-section {
    position: relative;
    background: linear-gradient(135deg,#0c0e11 0%,#111a1c 50%,#0c0e11 100%);
    border: 1px solid #1e2023;
    border-radius: 0.75rem;
    padding: 2rem 2.5rem;
    margin-bottom: 1.75rem;
    overflow: hidden;
    animation: fadeInUp 0.5s ease-out;
}
.hero-section::before {
    content:'';
    position:absolute; inset:0;
    background: radial-gradient(ellipse at 15% 50%,rgba(0,218,243,0.07) 0%,transparent 55%),
                radial-gradient(ellipse at 85% 50%,rgba(195,244,0,0.04) 0%,transparent 55%);
    pointer-events:none;
}
.hero-eyebrow {
    font-family:'Manrope',sans-serif; font-size:0.6rem; font-weight:800;
    color:#00daf3; text-transform:uppercase; letter-spacing:0.2em; margin-bottom:0.5rem;
}
.hero-title {
    font-family:'Manrope',sans-serif; font-size:2rem; font-weight:800;
    color:#e2e2e6; line-height:1.15; margin-bottom:0.45rem; letter-spacing:-0.03em;
}
.hero-title .accent {
    background:linear-gradient(90deg,#00daf3,#c3f5ff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.hero-subtitle {
    font-family:'Inter',sans-serif; font-size:0.83rem; color:#849396;
    max-width:500px; line-height:1.65; margin-bottom:1.2rem;
}
.hero-pills { display:flex; flex-wrap:wrap; gap:0.45rem; }
.hero-pill {
    display:inline-flex; align-items:center; gap:0.3rem;
    background:rgba(255,255,255,0.04); border:1px solid #282a2d;
    border-radius:2rem; padding:0.22rem 0.65rem;
    font-family:'Inter',sans-serif; font-size:0.63rem; font-weight:600; color:#bac9cc;
}
.hero-pill .dot {
    width:6px; height:6px; border-radius:50%; background:#c3f400;
    animation:blink-dot 2s infinite;
}
.hero-pill .dot.cyan  { background:#00daf3; }
.hero-pill .dot.amber { background:#ffba38; animation-delay:0.7s; }
.hero-ecg {
    position:absolute; right:2rem; top:50%; transform:translateY(-50%);
    pointer-events:none;
}
.hero-ecg svg path {
    stroke-dasharray:800;
    animation:ecg-draw 3.5s ease-in-out infinite;
}

/* ── PIPELINE TIMELINE ─────────────────────────────────────────────────── */
.pipeline-timeline {
    display:flex; align-items:center; flex-wrap:nowrap;
    padding:1.1rem 1.5rem; background:#111316;
    border:1px solid #1e2023; border-radius:0.5rem;
    margin-bottom:1.75rem; overflow-x:auto; gap:0;
}
.pipe-node { display:flex; flex-direction:column; align-items:center; gap:0.3rem; min-width:58px; }
.pipe-node-circle {
    width:34px; height:34px; border-radius:50%;
    display:flex; align-items:center; justify-content:center; font-size:0.95rem;
    background:#1e2023; border:1px solid #282a2d; transition:all 0.2s;
}
.pipe-node-circle.active { background:rgba(0,218,243,0.12); border-color:#00daf3; box-shadow:0 0 16px rgba(0,218,243,0.35); }
.pipe-node-circle.green  { background:rgba(195,244,0,0.08); border-color:#c3f400;  box-shadow:0 0 12px rgba(195,244,0,0.2); }
.pipe-node-circle.amber  { background:rgba(255,186,56,0.08); border-color:#ffba38; box-shadow:0 0 12px rgba(255,186,56,0.2); }
.pipe-node-label {
    font-family:'Manrope',sans-serif; font-size:0.52rem; font-weight:700;
    color:#3b494c; text-transform:uppercase; letter-spacing:0.06em;
    text-align:center; white-space:nowrap;
}
.pipe-node-label.active { color:#c3f5ff; }
.pipe-connector {
    flex:1; min-width:12px; height:1px; margin-bottom:1.3rem; margin-top:17px;
    background:linear-gradient(90deg,#1e2023,#3b494c,#1e2023);
}

/* ── DASHBOARD CARDS ───────────────────────────────────────────────────── */
.dash-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.7rem; margin-bottom:1.75rem; }
.dash-card {
    position:relative; background:#111316; border:1px solid #1e2023;
    border-radius:0.5rem; padding:1.1rem 1.25rem 0.9rem; overflow:hidden;
    transition:transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
    animation:fadeInUp 0.45s ease-out both;
}
.dash-card:hover { transform:translateY(-3px); }
.dash-card.cyan:hover  { box-shadow:0 8px 28px rgba(0,218,243,0.14); border-color:rgba(0,218,243,0.3); }
.dash-card.green:hover { box-shadow:0 8px 28px rgba(195,244,0,0.10); border-color:rgba(195,244,0,0.3); }
.dash-card.amber:hover { box-shadow:0 8px 28px rgba(255,186,56,0.10); border-color:rgba(255,186,56,0.3); }
.dash-card-bar { position:absolute; top:0; left:0; right:0; height:2px; }
.dash-card-bar.cyan  { background:linear-gradient(90deg,#00daf3,transparent); }
.dash-card-bar.green { background:linear-gradient(90deg,#c3f400,transparent); }
.dash-card-bar.amber { background:linear-gradient(90deg,#ffba38,transparent); }
.dash-card-num {
    position:absolute; top:0.8rem; right:1rem;
    font-family:'Manrope',sans-serif; font-size:0.58rem; font-weight:800;
    color:#282a2d; letter-spacing:0.05em;
}
.dash-card-icon { font-size:1.1rem; margin-bottom:0.35rem; margin-top:0.2rem; display:block; }
.dash-card-title { font-family:'Manrope',sans-serif; font-size:0.87rem; font-weight:700; color:#e2e2e6; line-height:1.3; }
.dash-card-desc  { font-family:'Inter',sans-serif; font-size:0.71rem; color:#849396; line-height:1.55; margin-top:0.3rem; }
.dash-card-tag {
    display:inline-block; margin-top:0.6rem;
    font-family:'Manrope',sans-serif; font-size:0.5rem; font-weight:800;
    text-transform:uppercase; letter-spacing:0.1em; padding:0.1rem 0.4rem; border-radius:0.2rem;
}
.dash-card-tag.cyan  { background:rgba(0,218,243,0.1);  color:#00daf3; }
.dash-card-tag.green { background:rgba(195,244,0,0.1);  color:#c3f400; }
.dash-card-tag.amber { background:rgba(255,186,56,0.1); color:#ffba38; }

/* ── QUICK START ───────────────────────────────────────────────────────── */
.qs-section {
    background:rgba(0,218,243,0.04); border:1px solid rgba(0,218,243,0.14);
    border-radius:0.5rem; padding:1.4rem 1.75rem; margin-bottom:1.25rem;
    position:relative; overflow:hidden;
}
.qs-section::before {
    content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
    background:linear-gradient(180deg,#00daf3,#c3f400,#ffba38);
}
.qs-eyebrow {
    font-family:'Manrope',sans-serif; font-size:0.6rem; font-weight:800;
    color:#00daf3; text-transform:uppercase; letter-spacing:0.15em; margin-bottom:0.9rem;
}
.qs-steps { display:flex; flex-direction:column; gap:0.6rem; }
.qs-step  { display:flex; align-items:flex-start; gap:0.7rem; }
.qs-num {
    min-width:20px; height:20px; border-radius:50%;
    background:rgba(0,218,243,0.12); border:1px solid rgba(0,218,243,0.3);
    font-family:'Manrope',sans-serif; font-size:0.58rem; font-weight:800; color:#00daf3;
    display:flex; align-items:center; justify-content:center;
}
.qs-text { font-family:'Inter',sans-serif; font-size:0.77rem; color:#bac9cc; line-height:1.55; padding-top:0.1rem; }

/* ── STATS FOOTER ──────────────────────────────────────────────────────── */
.stats-footer {
    display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;
    padding:0.7rem 1.25rem; background:#0c0e11;
    border:1px solid #1e2023; border-radius:0.375rem;
}
.stats-item { display:flex; align-items:center; gap:0.35rem; font-family:'Inter',sans-serif; font-size:0.62rem; color:#3b494c; }
.stats-item .val { color:#849396; font-weight:600; }
.stats-dot { width:4px; height:4px; border-radius:50%; background:#3b494c; }

/* ── SIDEBAR PREMIUM ───────────────────────────────────────────────────── */
.sb-brand {
    display:flex; align-items:center; gap:0.55rem;
    padding:0.4rem 0 0.9rem; border-bottom:1px solid #1e2023; margin-bottom:0.9rem;
}
.sb-brand-icon { font-size:1.35rem; animation:pulse-glow 3s ease-in-out infinite; display:inline-block; }
.sb-brand-name { font-family:'Manrope',sans-serif !important; font-size:0.82rem !important; font-weight:800 !important; color:#c3f5ff !important; margin:0 !important; letter-spacing:-0.02em; }
.sb-brand-sub  { font-family:'Inter',sans-serif; font-size:0.58rem; color:#3b494c; }
.sb-ver {
    margin-left:auto; font-family:'Manrope',sans-serif; font-size:0.48rem; font-weight:700;
    background:rgba(195,244,0,0.08); border:1px solid rgba(195,244,0,0.25); color:#c3f400;
    padding:0.12rem 0.38rem; border-radius:0.18rem; text-transform:uppercase; letter-spacing:0.05em; white-space:nowrap;
}
.sb-section-lbl {
    display:flex; align-items:center; gap:0.4rem;
    font-family:'Manrope',sans-serif; font-size:0.56rem; font-weight:800;
    text-transform:uppercase; letter-spacing:0.14em; color:#3b494c;
    padding:0.6rem 0 0.2rem; border-bottom:1px solid #1a1c1f; margin-bottom:0.25rem;
}
.sb-sync-pill {
    display:flex; align-items:center; justify-content:center; gap:0.35rem;
    margin-top:0.75rem; padding:0.38rem 0.8rem;
    background:rgba(195,244,0,0.05); border:1px solid rgba(195,244,0,0.12);
    border-radius:2rem; font-family:'Inter',sans-serif; font-size:0.6rem; color:#849396;
}
.sb-sync-pill .dot { width:5px; height:5px; border-radius:50%; background:#c3f400; animation:blink-dot 1.5s infinite; }
</style>
"""

def inject_stitch_theme():
    """Inject the full Stitch design system CSS."""
    st.markdown(STITCH_CSS, unsafe_allow_html=True)


def sentinel_header(page_title: str, badge: str = "", active_file: str = ""):
    """Render the Clinical Sentinel top app bar."""
    badge_html = f'<span class="sentinel-badge">{badge}</span>' if badge else ""
    file_html = f'<span style="font-size:0.7rem;color:#849396;font-family:Manrope,sans-serif;font-weight:600;">{active_file}</span>' if active_file else ""
    
    st.markdown(f"""
    <div class="sentinel-header">
        <span style="font-size:1.4rem;">🫀</span>
        <h1>Clinical Sentinel &nbsp;·&nbsp; {page_title}</h1>
        {badge_html}
        <div style="flex:1"></div>
        {file_html}
    </div>
    """, unsafe_allow_html=True)


def pipeline_status_bar(active_step: str):
    """Show the full pipeline status bar with highlighted active step."""
    steps = [
        ("📡", "Acquire"),
        ("🧹", "Filter"),
        ("❤️", "R-Peaks"),
        ("⏱️", "RR"),
        ("⚠️", "Ectopic"),
        ("📈", "HRV"),
        ("📊", "PSD"),
        ("🔬", "Nonlinear"),
    ]
    html_parts = []
    for icon, name in steps:
        cls = "pipeline-step active" if name == active_step else "pipeline-step"
        html_parts.append(f'<span class="{cls}">{icon} {name}</span>')
        if name != steps[-1][1]:
            html_parts.append('<span class="pipeline-arrow">›</span>')
    
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:0.3rem;align-items:center;margin-bottom:1.5rem;">{"".join(html_parts)}</div>',
        unsafe_allow_html=True
    )


def kpi_card(label: str, value: str, unit: str = "", accent: str = "primary", bar_pct: int = 0):
    """Render a single KPI card with optional progress bar."""
    accent_class = {"green": "accent-green", "amber": "accent-amber", "red": "accent-red"}.get(accent, "")
    value_class = {"green": "green", "amber": "amber"}.get(accent, "")
    bar_color = {"green": "#c3f400", "amber": "#ffba38", "red": "#ffb4ab"}.get(accent, "#00daf3")
    bar_shadow = {"green": "rgba(195,244,0,0.4)", "amber": "rgba(255,186,56,0.4)", "red": "rgba(255,180,171,0.4)"}.get(accent, "rgba(0,218,243,0.4)")
    bar_html = ""
    if bar_pct > 0:
        bar_html = f"""<div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(bar_pct,100)}%;background:{bar_color};box-shadow:0 0 8px {bar_shadow};"></div></div>"""
    return f"""
    <div class="kpi-card {accent_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {value_class}">{value}<span class="kpi-unit">{unit}</span></div>
        {bar_html}
    </div>
    """


def get_plot_layout(title_text: str = None, **overrides) -> dict:
    """
    Return a deep copy of PLOTLY_LAYOUT, optionally merged with overrides.
    """
    layout = copy.deepcopy(PLOTLY_LAYOUT)
    if title_text is not None:
        layout["title"] = dict(
            text=title_text if title_text.strip() else "Analysis Plot", 
            font=dict(family="Manrope, sans-serif", color=COLORS["primary"], size=14)
        )
    for k, v in overrides.items():
        layout[k] = v
    return layout

def set_layout(fig, title_text, xaxis_title="Time (s)", yaxis_title="Amplitude"):
    """
    Helper function to apply clinical sentinel theme and titles to a figure.
    Fixes the 'multiple values for keyword argument title' Plotly error.
    """
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=title_text,
            font=dict(family="Manrope, sans-serif", color=COLORS["primary"], size=14)
        ),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template="plotly_dark" # Base template as requested, overrides follow
    )
    # Re-apply some theme specifics that template might override
    fig.update_layout(
        paper_bgcolor=COLORS["surface_container_lowest"],
        plot_bgcolor=COLORS["surface_container_lowest"],
    )
    return fig

def save_all_figures(filename, charts_dict):
    """
    Helper to save charts as static images for reporting.
    """
    import os
    if not os.path.exists("reports/temp_plots"):
        os.makedirs("reports/temp_plots", exist_ok=True)
    
    paths = {}
    for key, img_bytes in charts_dict.items():
        path = f"reports/temp_plots/{filename}_{key}.png"
        with open(path, "wb") as f:
            f.write(img_bytes)
        paths[key] = path
    return paths


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def clinical_interpretation(text: str, kind: str = "info"):
    """Render a clinical interpretation card."""
    cls = {"warning": "warning", "success": "success"}.get(kind, "")
    icon = {"warning": "⚠️", "success": "✅"}.get(kind, "💡")
    title = {"warning": "Clinical Warning", "success": "Normal Range", "info": "Clinical Assessment"}.get(kind, "Assessment")
    st.markdown(f"""
    <div class="clinical-card {cls}" style="margin-top:1rem;">
        <div class="clinical-title">{icon} {title}</div>
        <div class="clinical-body">{text}</div>
    </div>
    """, unsafe_allow_html=True)
