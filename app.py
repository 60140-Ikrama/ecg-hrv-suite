"""Clinical Sentinel v3 — ICU Command Center Landing Dashboard"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from components.theme import inject_stitch_theme, sentinel_header, COLORS, kpi_card, set_layout
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(
    page_title="Clinical Sentinel v3 — ECG & HRV Suite",
    page_icon="🫀", layout="wide", initial_sidebar_state="expanded",
)

HOME_CSS = """<style>
.cmd-header{background:linear-gradient(135deg,#0c0e11 0%,#0d1418 50%,#0c0e11 100%);
  border:1px solid #1e2023;border-radius:.75rem;padding:1.5rem 2rem;margin-bottom:1.25rem;
  position:relative;overflow:hidden;}
.cmd-header::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 10% 50%,rgba(0,218,243,.08) 0%,transparent 55%),
             radial-gradient(ellipse at 90% 50%,rgba(179,136,255,.05) 0%,transparent 55%);
  pointer-events:none;}
.cmd-eyebrow{font-family:'Manrope',sans-serif;font-size:.55rem;font-weight:800;
  color:#00daf3;text-transform:uppercase;letter-spacing:.2em;margin-bottom:.4rem;}
.cmd-title{font-family:'Manrope',sans-serif;font-size:1.8rem;font-weight:900;
  color:#e2e2e6;line-height:1.15;letter-spacing:-.03em;}
.cmd-title .accent{background:linear-gradient(90deg,#00daf3,#b388ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.cmd-sub{font-family:'Inter',sans-serif;font-size:.78rem;color:#849396;
  max-width:520px;line-height:1.65;margin-top:.4rem;}
.status-bar{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-top:1rem;padding:.6rem .9rem;
  background:rgba(0,0,0,.3);border:1px solid #1e2023;border-radius:.4rem;}
.status-item{display:flex;align-items:center;gap:.35rem;font-family:'Inter',sans-serif;
  font-size:.63rem;color:#849396;}
.status-dot{width:7px;height:7px;border-radius:50%;animation:blink-dot 1.5s infinite;}
.vitals-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.65rem;margin-bottom:1.25rem;}
.vitals-card{background:#111316;border:1px solid #1e2023;border-radius:.6rem;
  padding:1rem 1.1rem;position:relative;overflow:hidden;transition:all .2s;}
.vitals-card:hover{border-color:#282a2d;transform:translateY(-2px);}
.vitals-card .top-bar{position:absolute;top:0;left:0;right:0;height:2.5px;}
.vitals-card .v-label{font-family:'Inter',sans-serif;font-size:.55rem;font-weight:700;
  color:#849396;text-transform:uppercase;letter-spacing:.12em;margin-bottom:.3rem;
  display:flex;align-items:center;gap:.35rem;}
.vitals-card .v-value{font-family:'Manrope',sans-serif;font-size:2rem;font-weight:900;
  color:#c3f5ff;line-height:1;}
.vitals-card .v-unit{font-size:.75rem;color:#849396;margin-left:.2rem;font-weight:400;}
.vitals-card .v-sub{font-family:'Inter',sans-serif;font-size:.65rem;color:#849396;margin-top:.3rem;}
.live-dot{width:7px;height:7px;border-radius:50%;background:#c3f400;
  display:inline-block;animation:blink-dot 1.5s infinite;}
.ai-panel{background:rgba(179,136,255,.05);border:1px solid rgba(179,136,255,.2);
  border-radius:.6rem;padding:1.1rem 1.25rem;}
.ai-panel-title{font-family:'Manrope',sans-serif;font-size:.6rem;font-weight:800;
  color:#b388ff;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.75rem;
  display:flex;align-items:center;gap:.4rem;}
.ai-finding{display:flex;align-items:flex-start;gap:.6rem;padding:.5rem 0;
  border-bottom:1px solid rgba(179,136,255,.08);font-family:'Inter',sans-serif;font-size:.75rem;color:#bac9cc;}
.ai-finding:last-child{border-bottom:none;}
.notif-row{display:flex;align-items:flex-start;gap:.6rem;padding:.5rem .7rem;
  border-bottom:1px solid #1e2023;font-family:'Inter',sans-serif;font-size:.72rem;}
.notif-row:last-child{border-bottom:none;}
.dash-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin-bottom:1.25rem;}
.dash-card3{background:#111316;border:1px solid #1e2023;border-radius:.5rem;
  padding:1rem 1.1rem;overflow:hidden;position:relative;transition:all .22s;}
.dash-card3:hover{transform:translateY(-2px);}
.dash-card3 .top-bar3{position:absolute;top:0;left:0;right:0;height:2px;}
.pipe-track{display:flex;align-items:center;overflow-x:auto;gap:0;
  padding:.9rem 1.2rem;background:#111316;border:1px solid #1e2023;
  border-radius:.5rem;margin-bottom:1.25rem;}
</style>"""

def _ecg_mini(signal, sfreq, height=140):
    if signal is None or len(signal) == 0:
        return None
    win = min(int(sfreq * 10), len(signal))
    seg = signal[-win:]
    t = np.arange(len(seg)) / sfreq
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t, y=seg, mode='lines', name='ECG',
        line=dict(color='#00ff88', width=1.2),
    ))
    fig.update_layout(
        paper_bgcolor='#050a07', plot_bgcolor='#050a07',
        margin=dict(l=0, r=0, t=0, b=0), height=height,
        xaxis=dict(showgrid=True, gridcolor='rgba(0,180,80,.12)', showticklabels=False,
                   zeroline=False, linecolor='transparent'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,180,80,.08)', showticklabels=False,
                   zeroline=False, linecolor='transparent'),
        showlegend=False, hovermode=False,
    )
    return fig

def _vitals_card(label, value, unit, sub, color, icon=""):
    return f"""
    <div class="vitals-card">
      <div class="top-bar" style="background:{color};"></div>
      <div class="v-label"><span class="live-dot" style="background:{color};"></span>{icon} {label}</div>
      <div class="v-value" style="color:{color};">{value}<span class="v-unit">{unit}</span></div>
      <div class="v-sub">{sub}</div>
    </div>"""

def main():
    inject_stitch_theme()
    render_sidebar_settings()
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    now = datetime.now().strftime("%H:%M:%S")
    active = st.session_state.get("active_file", "")
    metrics = st.session_state.get("metrics", {}).get(active, {})
    raw_signals = st.session_state.get("raw_signals", {})
    sfreq = st.session_state.get("sfreq", 250.0)
    n_files = len(raw_signals)
    alert_log = st.session_state.get("alert_log", [])
    n_alerts = sum(1 for a in alert_log if not a.get("ack"))

    # ── Command Center Header
    st.markdown(f"""
    <div class="cmd-header">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
        <div>
          <div class="cmd-eyebrow">🏥 Clinical Sentinel · Enterprise ECG/HRV Platform</div>
          <div class="cmd-title"><span class="accent">Cardiac Intelligence</span> Command Center</div>
          <div class="cmd-sub">
            Hospital-grade ECG acquisition, signal processing, HRV analytics and AI-powered
            cardiovascular risk stratification. Real-time · Research-level · Clinical-grade.
          </div>
        </div>
        <div style="text-align:right;font-family:'Manrope',sans-serif;">
          <div style="font-size:1.5rem;font-weight:900;color:#c3f5ff;">{now}</div>
          <div style="font-size:.6rem;color:#849396;margin-top:.2rem;">Session Active</div>
          <div style="font-size:.65rem;color:#b388ff;margin-top:.2rem;font-weight:700;">v3.0.0-Hospital</div>
        </div>
      </div>
      <div class="status-bar">
        <div class="status-item"><span class="status-dot" style="background:#c3f400;"></span>System Online</div>
        <div class="status-item"><span class="status-dot" style="background:{'#c3f400' if n_files>0 else '#3b494c'};"></span>Files: {n_files} Loaded</div>
        <div class="status-item"><span class="status-dot" style="background:{'#ff4b4b' if n_alerts>0 else '#c3f400'};"></span>Alerts: {n_alerts} Active</div>
        <div class="status-item"><span class="status-dot" style="background:{'#c3f400' if metrics else '#3b494c'};"></span>{'Analysis Ready' if metrics else 'Awaiting Data'}</div>
        <div class="status-item"><span class="status-dot" style="background:#849396;"></span>Cloud: Pending (Enterprise)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 8 Vitals KPI Cards
    hr    = metrics.get("Mean HR (bpm)", 0)
    sdnn  = metrics.get("SDNN (ms)", 0)
    rmssd = metrics.get("RMSSD (ms)", 0)
    lf_hf = metrics.get("LF/HF Ratio", 0)
    pnn50 = metrics.get("pNN50 (%)", 0)
    sqi   = st.session_state.get("sqi_cache", {}).get(active, {})
    sqi_s = sqi.get("overall_sqi", 0)

    hr_c     = "#ff4b4b" if (hr>120 or (0<hr<40)) else "#ffba38" if (hr>100 or (0<hr<50)) else "#c3f400"
    hrv_score = min(int(sdnn / 1.5), 100) if sdnn > 0 else 0
    stress    = min(int(lf_hf / 5 * 100), 100) if lf_hf > 0 else 0
    stress_c  = "#ff4b4b" if stress>70 else "#ffba38" if stress>40 else "#c3f400"
    auto_bal  = min(int((rmssd / 80) * 100), 100) if rmssd > 0 else 0

    no_data = "—" if not metrics else None

    cards_html = '<div class="vitals-grid">'
    cards_html += _vitals_card("Heart Rate", no_data or f"{hr:.0f}", "bpm",
                               "Normal 60–100 bpm", hr_c, "❤️")
    cards_html += _vitals_card("HRV Score",  no_data or str(hrv_score), "/100",
                               f"SDNN-based index", "#00daf3", "📊")
    cards_html += _vitals_card("Stress Index", no_data or f"{stress}", "%",
                               f"LF/HF: {lf_hf:.2f}" if lf_hf else "—", stress_c, "🧠")
    cards_html += _vitals_card("Arrhythmia Risk",
                               no_data or ("High" if sdnn<20 else "Mild" if sdnn<50 else "Low"),
                               "", f"SDNN: {sdnn:.1f} ms" if sdnn else "Run HRV analysis",
                               "#ff4b4b" if sdnn and sdnn<20 else "#ffba38" if sdnn and sdnn<50 else "#c3f400", "⚡")
    cards_html += _vitals_card("Signal Quality", no_data or f"{sqi_s:.0f}", "%",
                               sqi.get("quality_label","No data"), "#c3f400" if sqi_s>=70 else "#ffba38" if sqi_s>=40 else "#ff4b4b", "📡")
    cards_html += _vitals_card("pNN50", no_data or f"{pnn50:.1f}", "%",
                               "Parasympathetic index", "#b388ff", "🔬")
    cards_html += _vitals_card("Autonomic Balance", no_data or f"{auto_bal}", "%",
                               "Vagal tone estimate", "#00daf3", "⚖️")
    cards_html += _vitals_card("Files Loaded", str(n_files), "",
                               f"Active: {active[:20] if active else 'None'}", "#c3f5ff", "📁")
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    col_ecg, col_ai, col_notif = st.columns([4, 3, 2])

    # ── Live ECG Mini-Monitor
    with col_ecg:
        st.markdown("""
        <div style="font-family:'Manrope',sans-serif;font-size:.6rem;font-weight:800;
                    color:#849396;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem;
                    display:flex;align-items:center;gap:.4rem;">
          <span class="live-dot"></span> Live ECG Monitor
        </div>""", unsafe_allow_html=True)
        sig = raw_signals.get(active) if active else None
        ecg_fig = _ecg_mini(sig, sfreq)
        if ecg_fig:
            st.plotly_chart(ecg_fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown("""
            <div style="background:#050a07;border:1px solid #0a1a0f;border-radius:.4rem;
                        height:140px;display:flex;align-items:center;justify-content:center;">
              <div style="text-align:center;color:#1a3a25;">
                <div style="font-size:2rem;">📡</div>
                <div style="font-size:.7rem;font-family:'Manrope';font-weight:700;margin-top:.3rem;">
                  No Signal — Upload ECG to begin
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    # ── AI Intelligence Panel
    with col_ai:
        risk_r = st.session_state.get("risk_result",{})
        rl = risk_r.get("risk_level","—") if risk_r else ("High Risk" if metrics and sdnn<20 else "Mild Risk" if metrics and sdnn<50 else "Normal" if metrics else "—")
        rl_c = "#ff4b4b" if rl=="High Risk" else "#ffba38" if rl=="Mild Risk" else "#c3f400" if rl=="Normal" else "#849396"
        findings = []
        if metrics:
            if hr > 100: findings.append(("⚡","Tachycardia detected","#ffba38"))
            elif hr < 50 and hr > 0: findings.append(("⚡","Bradycardia detected","#ffba38"))
            if sdnn < 20: findings.append(("🚨","Very low HRV — cardiac risk","#ff4b4b"))
            elif sdnn < 50: findings.append(("⚠️","Reduced HRV variability","#ffba38"))
            if lf_hf > 3: findings.append(("🧠","Sympathetic overdrive","#ffba38"))
            if pnn50 > 40: findings.append(("✅","Strong vagal tone","#c3f400"))
            if sqi_s > 80: findings.append(("✅","Excellent signal quality","#c3f400"))
            if not findings: findings.append(("✅","All parameters nominal","#c3f400"))
        else:
            findings = [("ℹ️","Run full pipeline for insights","#849396")]
        st.markdown(f"""
        <div class="ai-panel">
          <div class="ai-panel-title">🤖 AI Cardiac Intelligence</div>
          <div style="margin-bottom:.75rem;">
            <div style="font-size:.58rem;color:#849396;font-family:'Inter';text-transform:uppercase;letter-spacing:.1em;">Risk Classification</div>
            <div style="font-family:'Manrope',sans-serif;font-size:1.3rem;font-weight:900;color:{rl_c};">{rl}</div>
            <div style="font-size:.65rem;color:#849396;">Confidence: {risk_r.get('confidence',0) if risk_r else '—'}%</div>
          </div>
          {''.join(f'''<div class="ai-finding"><span style="font-size:1rem;">{ic}</span>
            <div><div style="color:{c};font-weight:600;">{msg}</div></div></div>'''
            for ic,msg,c in findings[:5])}
        </div>""", unsafe_allow_html=True)

    # ── Smart Notifications
    with col_notif:
        notifs = []
        if active: notifs.append(("📁","#00daf3",f"Loaded: {active[:22]}","Just now"))
        if metrics: notifs.append(("✅","#c3f400","HRV analysis complete","Session"))
        if n_alerts > 0: notifs.append(("🚨","#ff4b4b",f"{n_alerts} active alert(s)","Monitor"))
        if sqi_s > 0: notifs.append(("📡","#00daf3",f"SQI: {sqi_s:.0f}% ({sqi.get('quality_label','?')})","Signal"))
        notifs.append(("🏥","#849396","System ready","v3.0.0"))
        st.markdown('<div style="font-family:\'Manrope\',sans-serif;font-size:.6rem;font-weight:800;color:#849396;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem;">🔔 Notifications</div>', unsafe_allow_html=True)
        notif_html = '<div style="background:#111316;border:1px solid #1e2023;border-radius:.5rem;overflow:hidden;">'
        for icon, c, msg, ts in notifs:
            notif_html += f"""
            <div class="notif-row" style="border-left:2px solid {c};">
              <span style="font-size:.9rem;">{icon}</span>
              <div style="flex:1;">
                <div style="color:#bac9cc;font-size:.72rem;">{msg}</div>
                <div style="color:#3b494c;font-size:.6rem;">{ts}</div>
              </div>
            </div>"""
        notif_html += '</div>'
        st.markdown(notif_html, unsafe_allow_html=True)

    # ── Pipeline Timeline
    steps = [
        ("📡","Acquire","active" if not active else "done"),
        ("🧹","Filter","done" if active in st.session_state.get("cleaned_signals",{}) else ""),
        ("❤️","R-Peaks","done" if active in st.session_state.get("rpeaks",{}) else ""),
        ("⏱️","RR","done" if active in st.session_state.get("raw_rr_intervals",{}) else ""),
        ("⚠️","Ectopics","done" if active in st.session_state.get("clean_rr_intervals",{}) else ""),
        ("📈","HRV","done" if metrics else ""),
        ("🔬","Nonlinear",""),("📁","Compare",""),
        ("🧠","AI Dx",""),("👥","Patients",""),
        ("🚨","Alerts",""),("📑","Report",""),
    ]
    nodes = ""
    for i,(icon,lbl,cls) in enumerate(steps):
        c = {"active":"#00daf3","done":"#c3f400"}.get(cls,"#282a2d")
        tc = {"active":"#c3f5ff","done":"#c3f400"}.get(cls,"#3b494c")
        nodes += f'<div style="display:flex;flex-direction:column;align-items:center;gap:.25rem;min-width:52px;"><div style="width:30px;height:30px;border-radius:50%;background:{c}22;border:1px solid {c};display:flex;align-items:center;justify-content:center;font-size:.8rem;">{icon}</div><div style="font-family:Manrope;font-size:.48rem;font-weight:700;color:{tc};text-transform:uppercase;letter-spacing:.05em;text-align:center;">{lbl}</div></div>'
        if i < len(steps)-1:
            nodes += '<div style="flex:1;min-width:8px;height:1px;margin-bottom:1.2rem;margin-top:15px;background:linear-gradient(90deg,#1e2023,#282a2d,#1e2023);"></div>'
    st.markdown(f"""
    <div style="font-family:'Manrope',sans-serif;font-size:.6rem;font-weight:800;color:#849396;
                text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem;">
      🔄 Analysis Pipeline
    </div>
    <div style="display:flex;align-items:center;padding:.9rem 1.2rem;background:#111316;
                border:1px solid #1e2023;border-radius:.5rem;margin-bottom:1.25rem;
                overflow-x:auto;gap:0;">{nodes}</div>
    """, unsafe_allow_html=True)

    # ── Dashboard Navigation Grid
    cards = [
        ("📡","Signal Acquisition","Upload ECG files · Batch support · URL download","#00daf3","01_Input_and_Acquisition","Input"),
        ("🧹","Preprocessing","SQI-aware filtering · Adaptive denoising · SNR analysis","#00daf3","02_Preprocessing","Filter"),
        ("❤️","R-Peak Detection","6 algorithms · Morphology · Beat classifier","#c3f400","03_R_Peak_Detection","Detection"),
        ("⏱️","RR & Ectopics","Tachogram · Ectopic correction · Rhythm patterns","#00daf3","04_RR_Intervals_and_Ectopics","Intervals"),
        ("📈","HRV Analysis","12 metrics · Autonomic balance · Trend analysis","#c3f400","05_HRV_Analysis_Time_Freq","HRV"),
        ("🔬","Non-Linear HRV","Poincaré · DFA · Sample Entropy · Complexity","#ffba38","06_Non_Linear_HRV","Nonlinear"),
        ("📁","Multi-File Compare","Radar chart · Statistical comparison · Rankings","#00daf3","07_Multi_File_Comparison","Compare"),
        ("📑","Report Generation","Patient report · Cardio expert report · PDF/DOCX","#c3f400","08_Report_Generation","Report"),
        ("🫀","Heart Disease Detect","Rule-based + ML · Risk gauge · Clinical flags","#ffba38","09_Heart_Disease_Detection","Clinical"),
        ("🧠","AI Diagnostic Center","Arrhythmia AI · Explainable AI · Narrative gen","#b388ff","10_AI_Diagnostic_Center","AI"),
        ("👥","Patient Management","Registry · Sessions · Risk stratification","#00daf3","11_Patient_Management","Registry"),
        ("🚨","Alert Monitor","ICU alerts · Thresholds · Wallboard mode","#ff4b4b","12_Alert_Monitor","Emergency"),
    ]
    st.markdown('<div style="font-family:\'Manrope\',sans-serif;font-size:.6rem;font-weight:800;color:#849396;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.75rem;">🗂 Clinical Dashboards</div>', unsafe_allow_html=True)
    html = '<div class="dash-grid3">'
    for i,(icon,title,desc,c,_,tag) in enumerate(cards):
        html += f"""
        <div class="dash-card3" style="animation:fadeInUp .45s ease-out {i*0.04:.2f}s both;">
          <div class="top-bar3" style="background:{c};"></div>
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.4rem;">
            <span style="font-size:1.1rem;">{icon}</span>
            <span style="font-family:'Manrope';font-size:.48rem;font-weight:800;text-transform:uppercase;
                         letter-spacing:.08em;background:{c}18;color:{c};padding:.08rem .35rem;
                         border-radius:.18rem;">{tag}</span>
          </div>
          <div style="font-family:'Manrope',sans-serif;font-size:.87rem;font-weight:700;color:#e2e2e6;
                      margin-bottom:.2rem;">{title}</div>
          <div style="font-family:'Inter',sans-serif;font-size:.7rem;color:#849396;line-height:1.5;">{desc}</div>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # ── Footer
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;padding:.6rem 1.2rem;
                background:#0c0e11;border:1px solid #1e2023;border-radius:.375rem;margin-top:.5rem;">
      <div style="font-family:'Inter',sans-serif;font-size:.6rem;color:#3b494c;">
        Version <span style="color:#849396;font-weight:600;">v3.0.0-Hospital</span>
      </div>
      <div style="width:3px;height:3px;border-radius:50%;background:#3b494c;"></div>
      <div style="font-size:.6rem;color:#3b494c;font-family:'Inter';">
        Dashboards <span style="color:#849396;font-weight:600;">12</span>
      </div>
      <div style="width:3px;height:3px;border-radius:50%;background:#3b494c;"></div>
      <div style="font-size:.6rem;color:#3b494c;font-family:'Inter';">
        Engine <span style="color:#849396;font-weight:600;">NeuroKit2 · SciPy · sklearn · Streamlit</span>
      </div>
      <div style="width:3px;height:3px;border-radius:50%;background:#3b494c;"></div>
      <div style="font-size:.6rem;color:#3b494c;font-family:'Inter';">
        Course <span style="color:#849396;font-weight:600;">Biomedical Signal Processing — OEL</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
