"""Dashboard 12 — Alert & Emergency Monitor"""
import streamlit as st
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, section_header, COLORS
from components.sidebar_settings import render_sidebar_settings

st.set_page_config(page_title="Alert Monitor · Clinical Sentinel", page_icon="🚨", layout="wide")

ALERT_CSS = """<style>
.alert-critical{background:linear-gradient(135deg,#1a0505,#200808);border:1.5px solid #ff4b4b;
  border-radius:.75rem;padding:1.25rem 1.5rem;margin-bottom:1rem;animation:pulse-red 2s infinite;}
@keyframes pulse-red{0%,100%{box-shadow:0 0 0 0 rgba(255,75,75,0);}
  50%{box-shadow:0 0 24px 4px rgba(255,75,75,.35);}}
.alert-warning{background:#1a1608;border:1.5px solid #ffba38;border-radius:.75rem;padding:1rem 1.25rem;margin-bottom:.75rem;}
.alert-stable{background:#12140c;border:1.5px solid #c3f400;border-radius:.75rem;padding:1rem 1.25rem;margin-bottom:.75rem;}
.alert-log-row{display:flex;justify-content:space-between;align-items:center;
  padding:.5rem .8rem;border-bottom:1px solid #1e2023;font-family:'Inter',sans-serif;font-size:.73rem;}
.alert-log-row:last-child{border-bottom:none;}
.thr-card{background:#1a1c1f;border:1px solid #1e2023;border-radius:.5rem;padding:.9rem 1.1rem;margin-bottom:.6rem;}
.thr-label{font-family:'Manrope',sans-serif;font-size:.65rem;font-weight:700;color:#849396;
  text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem;}
.icu-kpi{background:#0c0e11;border:2px solid;border-radius:.6rem;padding:1.2rem;text-align:center;}
.icu-val{font-family:'Manrope',sans-serif;font-size:2.8rem;font-weight:900;line-height:1;}
.icu-lbl{font-family:'Inter',sans-serif;font-size:.62rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.12em;color:#849396;margin-top:.3rem;}
.icu-unit{font-size:.9rem;font-weight:400;color:#849396;margin-left:.2rem;}
</style>"""

SEVERITY_ICONS = {"CRITICAL":"🚨","WARNING":"⚠️","STABLE":"✅","INFO":"ℹ️"}
SEVERITY_COLORS = {"CRITICAL":"#ff4b4b","WARNING":"#ffba38","STABLE":"#c3f400","INFO":"#00daf3"}

def _check_thresholds(metrics: dict, thresholds: dict) -> list:
    alerts = []
    now = datetime.now().strftime("%H:%M:%S")
    hr = metrics.get("Mean HR (bpm)", 0)
    sdnn = metrics.get("SDNN (ms)", 0)
    rmssd = metrics.get("RMSSD (ms)", 0)
    lf_hf = metrics.get("LF/HF Ratio", 0)

    if hr > thresholds.get("hr_high", 120):
        alerts.append({"severity":"CRITICAL","metric":"Heart Rate",
                       "message":f"HR {hr:.0f} bpm exceeds threshold ({thresholds['hr_high']} bpm)",
                       "time":now,"ack":False})
    elif hr < thresholds.get("hr_low", 40):
        alerts.append({"severity":"CRITICAL","metric":"Heart Rate",
                       "message":f"HR {hr:.0f} bpm below threshold ({thresholds['hr_low']} bpm)",
                       "time":now,"ack":False})
    if sdnn < thresholds.get("sdnn_low", 20):
        alerts.append({"severity":"WARNING","metric":"SDNN",
                       "message":f"SDNN {sdnn:.1f} ms critically low (threshold: {thresholds['sdnn_low']} ms)",
                       "time":now,"ack":False})
    if lf_hf > thresholds.get("lf_hf_high", 5.0):
        alerts.append({"severity":"WARNING","metric":"LF/HF Ratio",
                       "message":f"LF/HF {lf_hf:.2f} elevated — sympathetic overdrive",
                       "time":now,"ack":False})
    if rmssd < thresholds.get("rmssd_low", 10):
        alerts.append({"severity":"WARNING","metric":"RMSSD",
                       "message":f"RMSSD {rmssd:.1f} ms very low — reduced vagal tone",
                       "time":now,"ack":False})
    return alerts

def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 12 · Alert & Emergency Monitor", badge="ICU")
    st.markdown(ALERT_CSS, unsafe_allow_html=True)

    # Initialize alert log
    if "alert_log" not in st.session_state:
        st.session_state["alert_log"] = []
    if "alert_thresholds" not in st.session_state:
        st.session_state["alert_thresholds"] = {
            "hr_high": 120, "hr_low": 40, "sdnn_low": 20,
            "rmssd_low": 10, "lf_hf_high": 5.0
        }
    if "icu_mode" not in st.session_state:
        st.session_state["icu_mode"] = False

    # ICU wallboard toggle
    col_icu, col_refresh = st.columns([2,8])
    with col_icu:
        if st.button("🖥️ ICU Wallboard Mode" if not st.session_state["icu_mode"] else "🔙 Normal Mode",
                     use_container_width=True):
            st.session_state["icu_mode"] = not st.session_state["icu_mode"]
            st.rerun()

    # Get current metrics
    active = st.session_state.get("active_file","")
    metrics = {}
    if active and active in st.session_state.get("metrics",{}):
        metrics = st.session_state["metrics"][active]

    # Run threshold check
    if metrics:
        new_alerts = _check_thresholds(metrics, st.session_state["alert_thresholds"])
        for a in new_alerts:
            # Avoid duplicate
            existing = [e["message"] for e in st.session_state["alert_log"]]
            if a["message"] not in existing:
                st.session_state["alert_log"].insert(0, a)

    alert_log = st.session_state["alert_log"]
    active_crits = [a for a in alert_log if a["severity"]=="CRITICAL" and not a.get("ack")]
    active_warns = [a for a in alert_log if a["severity"]=="WARNING" and not a.get("ack")]

    # ── ICU WALLBOARD MODE
    if st.session_state["icu_mode"]:
        st.markdown("""
        <div style="text-align:center;padding:.4rem;background:#0c0e11;border:1px solid #1e2023;
                    border-radius:.4rem;margin-bottom:1rem;font-family:'Manrope',sans-serif;
                    font-size:.65rem;font-weight:800;color:#00daf3;text-transform:uppercase;letter-spacing:.2em;">
          🖥️ ICU Wallboard Mode — Critical KPIs Only
        </div>""", unsafe_allow_html=True)

        hr = metrics.get("Mean HR (bpm)", 0)
        sdnn = metrics.get("SDNN (ms)", 0)
        rmssd = metrics.get("RMSSD (ms)", 0)
        lf_hf = metrics.get("LF/HF Ratio", 0)

        hr_c = "#ff4b4b" if hr>120 or hr<40 else "#c3f400"
        sdnn_c = "#ff4b4b" if sdnn<20 else "#ffba38" if sdnn<50 else "#c3f400"

        cols = st.columns(4)
        kpis = [
            ("Heart Rate", f"{hr:.0f}", "bpm", hr_c),
            ("SDNN", f"{sdnn:.1f}", "ms", sdnn_c),
            ("RMSSD", f"{rmssd:.1f}", "ms", "#00daf3"),
            ("LF/HF", f"{lf_hf:.2f}", "", "#ffba38" if lf_hf>2.5 else "#c3f400"),
        ]
        for col, (lbl,val,unit,c) in zip(cols, kpis):
            with col:
                st.markdown(f"""
                <div class="icu-kpi" style="border-color:{c};">
                  <div class="icu-val" style="color:{c};">{val}<span class="icu-unit">{unit}</span></div>
                  <div class="icu-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        if active_crits:
            for a in active_crits:
                st.markdown(f"""
                <div class="alert-critical">
                  <div style="font-family:'Manrope',sans-serif;font-size:1.4rem;font-weight:900;color:#ff4b4b;">
                    🚨 CRITICAL — {a['metric']}
                  </div>
                  <div style="font-size:.9rem;color:#ffb4ab;margin-top:.3rem;">{a['message']}</div>
                  <div style="font-size:.7rem;color:#849396;margin-top:.2rem;">{a['time']}</div>
                </div>""", unsafe_allow_html=True)
        elif not metrics:
            st.info("No data loaded. Upload ECG and run analysis pipeline to enable monitoring.")
        else:
            st.markdown('<div class="alert-stable"><div style="font-family:Manrope;font-size:1.2rem;font-weight:800;color:#c3f400;">✅ ALL PARAMETERS STABLE</div></div>', unsafe_allow_html=True)
        return

    # ── NORMAL MODE
    # Active alert banners
    if active_crits:
        for a in active_crits:
            st.markdown(f"""
            <div class="alert-critical">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-family:'Manrope',sans-serif;font-size:1rem;font-weight:900;color:#ff4b4b;">
                    🚨 CRITICAL ALERT — {a['metric']}
                  </div>
                  <div style="font-size:.82rem;color:#ffb4ab;margin-top:.2rem;">{a['message']}</div>
                  <div style="font-size:.65rem;color:#849396;margin-top:.15rem;">Detected at {a['time']}</div>
                </div>
                <div style="font-size:2rem;">🔔</div>
              </div>
            </div>""", unsafe_allow_html=True)

    if active_warns:
        for a in active_warns:
            st.markdown(f"""
            <div class="alert-warning">
              <div style="font-family:'Manrope',sans-serif;font-size:.9rem;font-weight:800;color:#ffba38;">
                ⚠️ WARNING — {a['metric']}
              </div>
              <div style="font-size:.77rem;color:#bac9cc;margin-top:.15rem;">{a['message']}</div>
            </div>""", unsafe_allow_html=True)

    if not active_crits and not active_warns and metrics:
        st.markdown('<div class="alert-stable"><div style="font-family:Manrope;font-weight:800;color:#c3f400;">✅ All Parameters Within Normal Thresholds</div></div>', unsafe_allow_html=True)

    if not metrics:
        st.warning("⚠️ No analysis data found. Complete the HRV pipeline to enable alerting.")

    col_thresh, col_log = st.columns([1, 2])

    with col_thresh:
        section_header("Alert Thresholds")
        thr = st.session_state["alert_thresholds"]
        st.markdown('<div class="thr-card"><div class="thr-lbl">Heart Rate</div>', unsafe_allow_html=True)
        thr["hr_high"] = st.slider("HR Upper (bpm)", 80, 200, thr["hr_high"], 5, key="thr_hr_h")
        thr["hr_low"]  = st.slider("HR Lower (bpm)", 20, 60,  thr["hr_low"],  5, key="thr_hr_l")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="thr-card"><div class="thr-lbl">HRV Metrics</div>', unsafe_allow_html=True)
        thr["sdnn_low"]   = st.slider("SDNN Min (ms)", 5, 50, thr["sdnn_low"],   5, key="thr_sdnn")
        thr["rmssd_low"]  = st.slider("RMSSD Min (ms)", 5, 30, thr["rmssd_low"], 5, key="thr_rmssd")
        thr["lf_hf_high"] = st.slider("LF/HF Max", 2.0, 10.0, thr["lf_hf_high"], 0.5, key="thr_lfhf")
        st.markdown('</div>', unsafe_allow_html=True)

        # Alert stats
        total_a = len(alert_log)
        crit_a  = sum(1 for a in alert_log if a["severity"]=="CRITICAL")
        warn_a  = sum(1 for a in alert_log if a["severity"]=="WARNING")
        st.markdown(f"""
        <div style="background:#0c0e11;border:1px solid #1e2023;border-radius:.4rem;padding:.75rem 1rem;margin-top:.75rem;">
          <div style="font-family:'Manrope',sans-serif;font-size:.6rem;font-weight:800;
                      color:#849396;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem;">Session Alert Stats</div>
          <div style="display:flex;gap:1rem;">
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:800;color:#ff4b4b;">{crit_a}</div>
              <div style="font-size:.6rem;color:#849396;">Critical</div>
            </div>
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:800;color:#ffba38;">{warn_a}</div>
              <div style="font-size:.6rem;color:#849396;">Warning</div>
            </div>
            <div style="text-align:center;">
              <div style="font-size:1.5rem;font-weight:800;color:#c3f5ff;">{total_a}</div>
              <div style="font-size:.6rem;color:#849396;">Total</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        if alert_log and st.button("🗑️ Clear All Alerts", use_container_width=True):
            st.session_state["alert_log"] = []
            st.rerun()

    with col_log:
        section_header(f"Alert History Log ({len(alert_log)} events)")
        if not alert_log:
            st.markdown('<div style="padding:2rem;text-align:center;color:#849396;">No alerts triggered this session.</div>', unsafe_allow_html=True)
        else:
            log_html = '<div style="background:#111316;border:1px solid #1e2023;border-radius:.5rem;overflow:hidden;">'
            for a in alert_log:
                c = SEVERITY_COLORS.get(a["severity"],"#849396")
                icon = SEVERITY_ICONS.get(a["severity"],"ℹ️")
                ack_label = " · ✓ Acknowledged" if a.get("ack") else ""
                log_html += f"""
                <div class="alert-log-row" style="border-left:3px solid {c};">
                  <div>
                    <span style="color:{c};font-weight:700;">{icon} {a['severity']}</span>
                    <span style="color:#849396;margin-left:.5rem;">· {a['metric']}</span>
                    <span style="font-size:.65rem;color:#3b494c;">{ack_label}</span>
                    <div style="color:#bac9cc;margin-top:.15rem;">{a['message']}</div>
                  </div>
                  <div style="min-width:70px;text-align:right;color:#3b494c;font-size:.65rem;">{a['time']}</div>
                </div>"""
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

            # Acknowledge all criticals
            if active_crits and st.button("✅ Acknowledge All Critical Alerts", use_container_width=True):
                for a in st.session_state["alert_log"]:
                    if a["severity"] == "CRITICAL":
                        a["ack"] = True
                st.rerun()

    # Add demo alert button for testing
    st.markdown("---")
    st.markdown('<div style="font-size:.65rem;color:#3b494c;text-align:center;">Alert system monitors loaded analysis data. Run the full pipeline (Acquisition → HRV) to enable live alerting.</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
