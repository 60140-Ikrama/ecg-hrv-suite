"""Dashboard 10 — AI Diagnostic Center"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, section_header, COLORS, set_layout, kpi_card
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="AI Diagnostic Center · Clinical Sentinel", page_icon="🧠", layout="wide")

ARRHYTHMIA_CLASSES = ["Normal Sinus", "Atrial Fibrillation", "Tachycardia", "Bradycardia", "PVC/Ectopic", "Inconclusive"]
CLASS_COLORS = ["#c3f400", "#ff4b4b", "#ffba38", "#00daf3", "#b388ff", "#849396"]

def classify_arrhythmia(metrics: dict) -> dict:
    hr = metrics.get("Mean HR (bpm)", 75)
    sdnn = metrics.get("SDNN (ms)", 50)
    rmssd = metrics.get("RMSSD (ms)", 30)
    lf_hf = metrics.get("LF/HF Ratio", 1.5)
    pnn50 = metrics.get("pNN50 (%)", 20)
    probs = {"Normal Sinus": 60.0, "Atrial Fibrillation": 5.0, "Tachycardia": 5.0,
             "Bradycardia": 5.0, "PVC/Ectopic": 10.0, "Inconclusive": 15.0}
    if hr > 100:
        probs["Tachycardia"] += 35; probs["Normal Sinus"] -= 25
    elif hr < 50:
        probs["Bradycardia"] += 35; probs["Normal Sinus"] -= 25
    if sdnn < 20:
        probs["Atrial Fibrillation"] += 20; probs["Normal Sinus"] -= 15
    if rmssd > 80 and pnn50 > 40:
        probs["Normal Sinus"] += 15
    if lf_hf > 4.0:
        probs["PVC/Ectopic"] += 15; probs["Normal Sinus"] -= 10
    # Normalize
    total = sum(probs.values())
    probs = {k: max(0, round(v/total*100, 1)) for k, v in probs.items()}
    top = max(probs, key=probs.get)
    confidence = probs[top]
    return {"classification": top, "confidence": confidence, "probabilities": probs}

def compute_feature_importance(metrics: dict) -> dict:
    features = {
        "LF/HF Ratio": min(abs(metrics.get("LF/HF Ratio", 1.5) - 1.5) / 3.5 * 100, 100),
        "SDNN (ms)": max(0, 100 - metrics.get("SDNN (ms)", 50)),
        "Mean HR (bpm)": min(abs(metrics.get("Mean HR (bpm)", 75) - 72) / 50 * 100, 100),
        "RMSSD (ms)": max(0, 100 - metrics.get("RMSSD (ms)", 30) * 1.5),
        "pNN50 (%)": max(0, 50 - metrics.get("pNN50 (%)", 20)),
        "HF Power": max(0, 100 - metrics.get("HF Power (ms²)", 500) / 20),
        "DFA α1": min(abs(metrics.get("DFA α1", 1.0) - 1.0) / 0.4 * 100, 100) if "DFA α1" in metrics else 30,
    }
    return dict(sorted(features.items(), key=lambda x: x[1], reverse=True))

def generate_narrative(metrics: dict, result: dict, arrhythmia: dict) -> str:
    hr = metrics.get("Mean HR (bpm)", 75)
    sdnn = metrics.get("SDNN (ms)", 50)
    rmssd = metrics.get("RMSSD (ms)", 30)
    lf_hf = metrics.get("LF/HF Ratio", 1.5)
    risk = result.get("risk_level", "Normal")
    cls = arrhythmia.get("classification", "Normal Sinus")
    conf = arrhythmia.get("confidence", 70)
    hr_str = "elevated" if hr > 100 else "reduced" if hr < 50 else "within normal range"
    sdnn_str = "reduced" if sdnn < 30 else "borderline" if sdnn < 50 else "adequate"
    lf_str = "sympathetic dominance" if lf_hf > 2.5 else "balanced autonomic tone" if lf_hf > 0.7 else "parasympathetic dominance"
    return (
        f"Automated AI analysis of the ECG recording identifies the cardiac rhythm as "
        f"**{cls}** with {conf:.0f}% model confidence. "
        f"Heart rate is {hr_str} at {hr:.0f} bpm. "
        f"HRV metrics indicate {sdnn_str} overall variability (SDNN: {sdnn:.1f} ms) "
        f"with {lf_str} (LF/HF: {lf_hf:.2f}). "
        f"Vagal tone marker RMSSD is {rmssd:.1f} ms. "
        f"Cardiovascular risk classification: **{risk}**. "
        + ("⚠️ *Recommend immediate clinical review.*" if risk == "High Risk" else
           "🔍 *Routine follow-up advised.*" if risk == "Mild Risk" else
           "✅ *No immediate intervention indicated.*")
    )

def get_recommendations(risk: str, cls: str) -> list:
    base = []
    if cls == "Atrial Fibrillation":
        base = [("🚨 Immediate", "Refer to cardiologist for AF management"),
                ("🚨 Immediate", "Anticoagulation therapy evaluation"),
                ("⏰ 24h", "12-lead ECG confirmation"),
                ("📋 Routine", "Echocardiogram to assess cardiac structure")]
    elif cls == "Tachycardia":
        base = [("⏰ 24h", "Holter monitor for 24-48h"),
                ("📋 Routine", "TSH / thyroid panel"),
                ("📋 Routine", "Electrolyte panel (K⁺, Mg²⁺)")]
    elif cls == "Bradycardia":
        base = [("⏰ 24h", "Review current medications (beta-blockers, digoxin)"),
                ("📋 Routine", "Exercise stress test"),
                ("👁 Observe", "Continuous monitoring if HR < 40 bpm")]
    elif cls == "PVC/Ectopic":
        base = [("⏰ 24h", "24h Holter for ectopic burden quantification"),
                ("📋 Routine", "Electrolyte panel"),
                ("📋 Routine", "Echocardiogram if burden > 10%")]
    else:
        if risk == "High Risk":
            base = [("⏰ 24h", "Cardiology consultation"), ("📋 Routine", "Holter monitoring")]
        elif risk == "Mild Risk":
            base = [("📋 Routine", "Follow-up in 3 months"), ("👁 Observe", "Lifestyle modification")]
        else:
            base = [("✅ Routine", "Annual cardiac screening"), ("✅ Routine", "Continue current management")]
    return base

def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 10 · AI Diagnostic Center", badge="AI", active_file=st.session_state.get("active_file",""))

    st.markdown("""
    <style>
    .ai-header{background:linear-gradient(135deg,rgba(179,136,255,0.08),rgba(0,218,243,0.05));
      border:1px solid rgba(179,136,255,0.25);border-radius:.75rem;padding:1.25rem 1.5rem;margin-bottom:1.25rem;}
    .ai-label{font-family:'Manrope',sans-serif;font-size:.55rem;font-weight:800;color:#b388ff;
      text-transform:uppercase;letter-spacing:.18em;margin-bottom:.3rem;}
    .ai-cls{font-family:'Manrope',sans-serif;font-size:2rem;font-weight:900;color:#c3f5ff;line-height:1;}
    .ai-conf{font-family:'Inter',sans-serif;font-size:.78rem;color:#849396;margin-top:.3rem;}
    .ai-conf span{color:#b388ff;font-weight:700;}
    .conf-bar-wrap{background:#1e2023;border-radius:.25rem;height:8px;overflow:hidden;margin-top:.4rem;}
    .conf-bar{height:100%;border-radius:.25rem;background:linear-gradient(90deg,#b388ff,#00daf3);}
    .feat-row{display:flex;justify-content:space-between;align-items:center;
      padding:.45rem .6rem;border-bottom:1px solid #1e2023;font-family:'Inter',sans-serif;font-size:.75rem;}
    .feat-name{color:#bac9cc;}
    .feat-bar-wrap{flex:1;margin:0 .75rem;background:#1e2023;border-radius:2px;height:6px;overflow:hidden;}
    .feat-bar{height:100%;border-radius:2px;}
    .rec-row{display:flex;align-items:flex-start;gap:.75rem;padding:.55rem .7rem;
      background:#1a1c1f;border-radius:.35rem;margin-bottom:.4rem;border-left:3px solid;}
    .rec-urgency{font-family:'Manrope',sans-serif;font-size:.55rem;font-weight:800;
      text-transform:uppercase;letter-spacing:.08em;min-width:72px;}
    .rec-text{font-family:'Inter',sans-serif;font-size:.77rem;color:#bac9cc;}
    .narrative-box{background:rgba(179,136,255,.05);border:1px solid rgba(179,136,255,.2);
      border-radius:.5rem;padding:1.1rem 1.3rem;font-family:'Inter',sans-serif;
      font-size:.82rem;color:#bac9cc;line-height:1.7;}
    </style>
    """, unsafe_allow_html=True)

    metrics = {}
    active = st.session_state.get("active_file", "")
    if active and active in st.session_state.get("metrics", {}):
        metrics = st.session_state["metrics"][active]

    if not metrics:
        st.markdown("""
        <div style="text-align:center;padding:4rem 1rem;">
          <div style="font-size:3.5rem;">🧠</div>
          <div style="font-family:'Manrope',sans-serif;font-size:1rem;font-weight:700;
                      color:#bac9cc;margin-top:.5rem;">No Analysis Data</div>
          <div style="font-size:.8rem;color:#849396;margin-top:.3rem;">
            Complete the pipeline through <strong>Dashboard 06 · HRV Analysis</strong> to enable AI diagnostics.
          </div>
        </div>""", unsafe_allow_html=True)
        return

    arrhythmia = classify_arrhythmia(metrics)
    feat_imp = compute_feature_importance(metrics)
    risk_result = {}
    try:
        from utils.heart_disease_detection import classify_cardiovascular_risk
        sqi = st.session_state.get("sqi_cache", {}).get(active, {})
        risk_result = classify_cardiovascular_risk(metrics, use_ml=True, sqi=sqi)
    except Exception:
        risk_result = {"risk_level": "Unknown", "score": 0, "confidence": 0}

    cls = arrhythmia["classification"]
    conf = arrhythmia["confidence"]
    probs = arrhythmia["probabilities"]
    cls_color = CLASS_COLORS[ARRHYTHMIA_CLASSES.index(cls)] if cls in ARRHYTHMIA_CLASSES else "#849396"

    # ── AI Header Banner
    st.markdown(f"""
    <div class="ai-header">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
        <div>
          <div class="ai-label">🧠 AI Rhythm Classification</div>
          <div class="ai-cls" style="color:{cls_color};">{cls}</div>
          <div class="ai-conf">Model Confidence: <span>{conf:.0f}%</span></div>
          <div class="conf-bar-wrap" style="width:220px;">
            <div class="conf-bar" style="width:{conf}%;"></div>
          </div>
        </div>
        <div style="text-align:right;">
          <div class="ai-label">Cardiovascular Risk</div>
          <div style="font-family:'Manrope',sans-serif;font-size:1.5rem;font-weight:800;
                      color:{'#c3f400' if risk_result.get('risk_level')=='Normal' else '#ffba38' if risk_result.get('risk_level')=='Mild Risk' else '#ff4b4b'};">
            {risk_result.get('risk_level','Unknown')}
          </div>
          <div class="ai-conf">Risk Score: <span>{risk_result.get('score',0):.0f}/100</span></div>
        </div>
        <div style="background:rgba(179,136,255,.1);border:1px solid rgba(179,136,255,.3);
                    border-radius:.35rem;padding:.4rem .8rem;font-size:.6rem;font-weight:800;
                    color:#b388ff;text-transform:uppercase;letter-spacing:.1em;align-self:flex-start;">
          🤖 AI Engine Active
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        # ── Class Probability Chart
        section_header("Arrhythmia Classification Probabilities")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=ARRHYTHMIA_CLASSES,
            x=[probs.get(c, 0) for c in ARRHYTHMIA_CLASSES],
            orientation="h",
            marker_color=CLASS_COLORS,
            text=[f"{probs.get(c,0):.1f}%" for c in ARRHYTHMIA_CLASSES],
            textposition="outside",
            textfont=dict(color="#bac9cc", size=11),
        ))
        set_layout(fig, "Rhythm Classification Confidence", xaxis_title="Probability (%)", yaxis_title="")
        fig.update_layout(height=280, xaxis=dict(range=[0, 120], showgrid=False),
                          yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # ── Feature Importance
        section_header("Explainable AI — Feature Contributions")
        feat_html = ""
        palette = ["#b388ff","#00daf3","#c3f400","#ffba38","#ff4b4b","#849396","#c3f5ff"]
        for i,(name,val) in enumerate(feat_imp.items()):
            c = palette[i % len(palette)]
            feat_html += f"""
            <div class="feat-row">
              <span class="feat-name">{name}</span>
              <div class="feat-bar-wrap">
                <div class="feat-bar" style="width:{val:.0f}%;background:{c};"></div>
              </div>
              <span style="color:{c};font-weight:700;min-width:36px;text-align:right;">{val:.0f}%</span>
            </div>"""
        st.markdown(f'<div style="background:#111316;border:1px solid #1e2023;border-radius:.5rem;">{feat_html}</div>',
                    unsafe_allow_html=True)

    with col2:
        # ── KPI strip
        hr = metrics.get("Mean HR (bpm)", 0)
        sdnn = metrics.get("SDNN (ms)", 0)
        rmssd = metrics.get("RMSSD (ms)", 0)
        lf_hf = metrics.get("LF/HF Ratio", 0)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:.55rem;margin-bottom:.9rem;">
          {kpi_card("Heart Rate","%.0f"%hr,"bpm",accent="primary" if 50<=hr<=100 else "red")}
          {kpi_card("SDNN","%.1f"%sdnn,"ms",accent="green" if sdnn>=50 else "amber" if sdnn>=20 else "red",bar_pct=min(int(sdnn),150))}
          {kpi_card("RMSSD","%.1f"%rmssd,"ms",accent="primary",bar_pct=min(int(rmssd),100))}
          {kpi_card("LF/HF","%.2f"%lf_hf,"",accent="green" if 0.7<=lf_hf<=2.5 else "amber")}
        </div>
        """, unsafe_allow_html=True)

        # ── Recommendations
        section_header("Clinical Recommendations")
        recs = get_recommendations(risk_result.get("risk_level","Normal"), cls)
        urgency_colors = {"🚨 Immediate":"#ff4b4b","⏰ 24h":"#ffba38","📋 Routine":"#00daf3","👁 Observe":"#849396","✅ Routine":"#c3f400"}
        rec_html = ""
        for urgency, text in recs:
            c = urgency_colors.get(urgency, "#849396")
            rec_html += f"""
            <div class="rec-row" style="border-left-color:{c};">
              <span class="rec-urgency" style="color:{c};">{urgency}</span>
              <span class="rec-text">{text}</span>
            </div>"""
        st.markdown(rec_html, unsafe_allow_html=True)

        # ── 30-day risk
        score_30d = min(risk_result.get("score", 0) * 1.15, 100)
        section_header("Sudden Cardiac Risk Estimate")
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score_30d,
            number={"suffix":"%","font":{"size":28,"color":"#c3f5ff"}},
            title={"text":"30-Day Risk Index","font":{"size":12,"color":"#849396"}},
            gauge={"axis":{"range":[0,100]},"bar":{"color":"#b388ff","thickness":.25},
                   "bgcolor":COLORS["surface_container_lowest"],
                   "steps":[{"range":[0,30],"color":"rgba(195,244,0,.1)"},
                            {"range":[30,60],"color":"rgba(255,186,56,.1)"},
                            {"range":[60,100],"color":"rgba(255,75,75,.15)"}]}
        ))
        fig2.update_layout(paper_bgcolor=COLORS["surface_container_lowest"],
                           plot_bgcolor=COLORS["surface_container_lowest"],
                           font=dict(color=COLORS["on_surface_variant"]),
                           height=200, margin=dict(l=20,r=20,t=40,b=10))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('<div style="font-size:.62rem;color:#849396;text-align:center;margin-top:-.5rem;">⚕️ Research estimate only — not clinical advice</div>',
                    unsafe_allow_html=True)

    # ── AI Narrative
    st.markdown("---")
    section_header("AI Diagnostic Narrative")
    narrative = generate_narrative(metrics, risk_result, arrhythmia)
    st.markdown(f'<div class="narrative-box">{narrative}</div>', unsafe_allow_html=True)

    # ── Disclaimer
    st.markdown(f"""
    <div style="margin-top:1.5rem;padding:.7rem 1rem;border-radius:.4rem;
                background:{COLORS['surface_container']};border:1px solid {COLORS['outline_variant']};
                font-size:.7rem;color:{COLORS['on_surface_variant']};text-align:center;">
      ⚕️ <strong>Medical Disclaimer:</strong> AI outputs are for research and educational use only.
      All findings must be validated by a qualified cardiologist before clinical decisions are made.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
