"""
Stitch Design System: CSS injection and shared UI components.
Applies Clinical Sentinel theme tokens to Streamlit.
"""
import streamlit as st

# === STITCH DESIGN TOKENS ===
COLORS = {
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
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["surface_container_lowest"],
    plot_bgcolor=COLORS["surface_container_lowest"],
    font=dict(family="Inter, sans-serif", color=COLORS["on_surface_variant"], size=11),
    title_font=dict(family="Manrope, sans-serif", color=COLORS["primary"], size=14),
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
#MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
.stDeployButton { display: none !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

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
section[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
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
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: #c3f5ff !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
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
