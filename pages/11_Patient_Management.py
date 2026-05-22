"""Dashboard 11 — Patient Management System"""
import streamlit as st
import json
from datetime import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.theme import inject_stitch_theme, sentinel_header, section_header, COLORS
from components.sidebar_settings import render_sidebar_settings
from utils.patient_db import (load_patients, save_patient, delete_patient,
                               add_session, search_patients, get_demo_patients)

st.set_page_config(page_title="Patient Management · Clinical Sentinel", page_icon="👥", layout="wide")

RISK_STYLE = {
    "High Risk":  {"color":"#ff4b4b","bg":"#1a0d0d","border":"#ff4b4b","icon":"🚨"},
    "Mild Risk":  {"color":"#ffba38","bg":"#1a1608","border":"#ffba38","icon":"⚠️"},
    "Normal":     {"color":"#c3f400","bg":"#12140c","border":"#c3f400","icon":"✅"},
    "Unknown":    {"color":"#849396","bg":"#1a1c1f","border":"#3b494c","icon":"❓"},
}

PM_CSS = """
<style>
.pt-card{background:#111316;border:1px solid #1e2023;border-radius:.6rem;
  padding:1.1rem 1.2rem;transition:all .22s ease;cursor:pointer;position:relative;overflow:hidden;}
.pt-card:hover{border-color:#3b494c;transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.3);}
.pt-card-top{height:3px;position:absolute;top:0;left:0;right:0;}
.pt-name{font-family:'Manrope',sans-serif;font-size:.97rem;font-weight:800;color:#e2e2e6;margin-bottom:.15rem;}
.pt-meta{font-family:'Inter',sans-serif;font-size:.7rem;color:#849396;margin-bottom:.5rem;}
.pt-tag{display:inline-block;font-family:'Manrope',sans-serif;font-size:.5rem;font-weight:800;
  text-transform:uppercase;letter-spacing:.08em;padding:.1rem .4rem;border-radius:.2rem;margin-right:.3rem;}
.pt-risk{font-family:'Manrope',sans-serif;font-size:.75rem;font-weight:700;margin-top:.4rem;}
.sess-row{display:flex;justify-content:space-between;align-items:center;padding:.5rem .7rem;
  background:#1e2023;border-radius:.3rem;margin-bottom:.35rem;font-family:'Inter',sans-serif;font-size:.73rem;}
.sess-time{color:#849396;font-size:.65rem;}
.field-lbl{font-family:'Manrope',sans-serif;font-size:.58rem;font-weight:800;
  text-transform:uppercase;letter-spacing:.1em;color:#849396;margin-bottom:.2rem;}
</style>"""

def _risk_badge(risk: str) -> str:
    s = RISK_STYLE.get(risk, RISK_STYLE["Unknown"])
    return (f'<span style="background:{s["bg"]};border:1px solid {s["border"]};'
            f'color:{s["color"]};font-family:Manrope;font-size:.6rem;font-weight:800;'
            f'padding:.15rem .5rem;border-radius:.2rem;">{s["icon"]} {risk}</span>')

def _patient_card(p: dict) -> str:
    s = RISK_STYLE.get(p.get("risk_level","Unknown"), RISK_STYLE["Unknown"])
    tags_html = "".join(
        f'<span class="pt-tag" style="background:{s["bg"]};color:{s["color"]};border:1px solid {s["border"]}55;">{t}</span>'
        for t in p.get("tags", [])
    )
    sessions = p.get("sessions", [])
    last_sess = f"Last session: {sessions[-1]['timestamp'][:10]}" if sessions else "No sessions yet"
    conds = ", ".join(p.get("conditions", [])) or "No conditions recorded"
    return f"""
    <div class="pt-card">
      <div class="pt-card-top" style="background:{s['color']};"></div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div class="pt-name">{p.get('name','Unknown')}</div>
          <div class="pt-meta">ID: {p.get('id','—')} · {p.get('age','?')}y · {p.get('sex','?')} · {last_sess}</div>
          <div style="font-size:.72rem;color:#bac9cc;margin-bottom:.4rem;">{conds}</div>
          {tags_html}
        </div>
        <div style="text-align:right;">
          {_risk_badge(p.get('risk_level','Unknown'))}
          <div style="font-family:Manrope;font-size:.7rem;color:#849396;margin-top:.3rem;">
            Score: <strong style="color:{s['color']};">{p.get('risk_score',0):.0f}/100</strong>
          </div>
          <div style="font-size:.6rem;color:#3b494c;margin-top:.2rem;">{len(sessions)} session(s)</div>
        </div>
      </div>
    </div>"""

def main():
    inject_stitch_theme()
    render_sidebar_settings()
    sentinel_header("Dashboard 11 · Patient Management", badge="Registry")
    st.markdown(PM_CSS, unsafe_allow_html=True)

    # Load patients — seed demo data if empty
    patients = load_patients()
    if not patients:
        for demo in get_demo_patients():
            save_patient(demo)
        patients = load_patients()

    tab_list, tab_add, tab_detail = st.tabs(["👥 Patient Registry", "➕ Add Patient", "📋 Session History"])

    # ── Tab 1: Registry
    with tab_list:
        c_search, c_risk, c_sort = st.columns([3, 2, 2])
        with c_search:
            query = st.text_input("🔍 Search patients", placeholder="Name or ID...", label_visibility="collapsed")
        with c_risk:
            risk_f = st.selectbox("Risk Filter", ["All","Normal","Mild Risk","High Risk"], label_visibility="collapsed")
        with c_sort:
            sort_by = st.selectbox("Sort By", ["Last Updated","Name","Risk Score"], label_visibility="collapsed")

        results = search_patients(query, risk_f)
        if sort_by == "Name":
            results = sorted(results, key=lambda x: x.get("name",""))
        elif sort_by == "Risk Score":
            results = sorted(results, key=lambda x: x.get("risk_score", 0), reverse=True)

        # Stats bar
        total = len(patients)
        high_r = sum(1 for p in patients.values() if p.get("risk_level") == "High Risk")
        mild_r = sum(1 for p in patients.values() if p.get("risk_level") == "Mild Risk")
        normal_r = sum(1 for p in patients.values() if p.get("risk_level") == "Normal")
        st.markdown(f"""
        <div style="display:flex;gap:1rem;flex-wrap:wrap;margin:.75rem 0;padding:.7rem 1rem;
                    background:#0c0e11;border:1px solid #1e2023;border-radius:.4rem;">
          <div style="font-family:'Inter',sans-serif;font-size:.7rem;color:#849396;">
            Total Patients: <strong style="color:#c3f5ff;">{total}</strong>
          </div>
          <div style="width:1px;background:#1e2023;"></div>
          <div style="font-size:.7rem;font-family:'Inter',sans-serif;color:#ff4b4b;">
            🚨 High Risk: <strong>{high_r}</strong>
          </div>
          <div style="font-size:.7rem;font-family:'Inter',sans-serif;color:#ffba38;">
            ⚠️ Mild Risk: <strong>{mild_r}</strong>
          </div>
          <div style="font-size:.7rem;font-family:'Inter',sans-serif;color:#c3f400;">
            ✅ Normal: <strong>{normal_r}</strong>
          </div>
          <div style="margin-left:auto;font-size:.65rem;color:#3b494c;display:flex;align-items:center;gap:.4rem;">
            <span style="width:6px;height:6px;border-radius:50%;background:#c3f400;display:inline-block;animation:blink-dot 1.5s infinite;"></span>
            Cloud Sync Pending (Enterprise Feature)
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not results:
            st.info("No patients match your search criteria.")
        else:
            cols = st.columns(2)
            for i, p in enumerate(results):
                with cols[i % 2]:
                    st.markdown(_patient_card(p), unsafe_allow_html=True)
                    pid = p.get("id","")
                    c1, c2, c3 = st.columns([2,1,1])
                    with c1:
                        st.session_state.setdefault("selected_patient", pid)
                        if st.button("📋 View Details", key=f"view_{pid}", use_container_width=True):
                            st.session_state["selected_patient"] = pid
                    with c2:
                        tags = p.get("tags", [])
                        if st.button("🚨 Critical" if "URGENT" not in tags else "✅ Clear", key=f"tag_{pid}", use_container_width=True):
                            if "URGENT" in tags:
                                tags.remove("URGENT")
                            else:
                                tags.append("URGENT")
                            p["tags"] = tags
                            save_patient(p)
                            st.rerun()
                    with c3:
                        if st.button("🗑️", key=f"del_{pid}", use_container_width=True):
                            delete_patient(pid)
                            st.rerun()
                    st.markdown("<div style='margin-bottom:.5rem;'></div>", unsafe_allow_html=True)

    # ── Tab 2: Add Patient
    with tab_add:
        st.markdown('<div class="field-lbl">Patient Information</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Full Name", placeholder="Ahmad Raza")
            age = st.number_input("Age", min_value=1, max_value=120, value=45)
        with c2:
            sex = st.selectbox("Sex", ["Male","Female","Other"])
            pid_manual = st.text_input("Patient ID (auto if blank)", placeholder="PT004")
        with c3:
            conditions_raw = st.text_area("Medical Conditions (one per line)", placeholder="Hypertension\nDiabetes Type 2")
            medications_raw = st.text_area("Medications (one per line)", placeholder="Metoprolol 50mg\nAspirin 81mg")

        notes = st.text_area("Clinical Notes", placeholder="Initial assessment notes...")
        col_save, col_link = st.columns([1,2])
        with col_save:
            if st.button("💾 Save Patient", use_container_width=True, type="primary"):
                if name.strip():
                    new_p = {
                        "name": name.strip(),
                        "age": age, "sex": sex,
                        "id": pid_manual.strip() or None,
                        "conditions": [c.strip() for c in conditions_raw.split("\n") if c.strip()],
                        "medications": [m.strip() for m in medications_raw.split("\n") if m.strip()],
                        "risk_level": "Unknown", "risk_score": 0, "tags": [],
                        "notes": notes.strip(),
                    }
                    new_id = save_patient(new_p)
                    st.success(f"✅ Patient saved — ID: **{new_id}**")
                    st.rerun()
                else:
                    st.error("Patient name is required.")
        with col_link:
            active_file = st.session_state.get("active_file","")
            if active_file and st.button(f"🔗 Link '{active_file}' to Selected Patient", use_container_width=True):
                sel = st.session_state.get("selected_patient","")
                if sel:
                    metrics = st.session_state.get("metrics",{}).get(active_file,{})
                    risk_r = st.session_state.get("risk_result",{})
                    add_session(sel, {
                        "file": active_file,
                        "risk_level": risk_r.get("risk_level","Unknown"),
                        "risk_score": risk_r.get("score",0),
                        "hrv_score": round(min(metrics.get("SDNN (ms)",0)/100*100,100),1),
                        "notes": "Linked from active session."
                    })
                    st.success(f"Session linked to patient {sel}")
                else:
                    st.warning("Select a patient in the Registry tab first.")

    # ── Tab 3: Session History
    with tab_detail:
        all_patients = load_patients()
        sel_pid = st.session_state.get("selected_patient","")
        pt_names = {pid: p.get("name","?") for pid, p in all_patients.items()}
        if not pt_names:
            st.info("No patients registered yet.")
            return

        chosen = st.selectbox("Select Patient", options=list(pt_names.keys()),
                              format_func=lambda x: f"{pt_names[x]} ({x})",
                              index=list(pt_names.keys()).index(sel_pid) if sel_pid in pt_names else 0)
        pt = all_patients.get(chosen, {})

        # Patient banner
        s = RISK_STYLE.get(pt.get("risk_level","Unknown"), RISK_STYLE["Unknown"])
        st.markdown(f"""
        <div style="background:{s['bg']};border:1.5px solid {s['border']};border-radius:.6rem;
                    padding:1rem 1.25rem;margin-bottom:1rem;display:flex;gap:1.5rem;align-items:center;">
          <div style="font-size:2.5rem;">{s['icon']}</div>
          <div style="flex:1;">
            <div style="font-family:'Manrope',sans-serif;font-size:1.2rem;font-weight:900;color:#e2e2e6;">
              {pt.get('name','?')}
            </div>
            <div style="font-size:.72rem;color:#849396;font-family:'Inter',sans-serif;margin-top:.15rem;">
              ID: {pt.get('id','?')} · {pt.get('age','?')} years · {pt.get('sex','?')} ·
              Conditions: {', '.join(pt.get('conditions',[])) or 'None'}
            </div>
            <div style="font-size:.72rem;color:#bac9cc;margin-top:.2rem;">
              Medications: {', '.join(pt.get('medications',[])) or 'None'}
            </div>
          </div>
          <div style="text-align:right;">
            {_risk_badge(pt.get('risk_level','Unknown'))}
            <div style="font-size:.65rem;color:#3b494c;margin-top:.3rem;">
              {len(pt.get('sessions',[]))} recorded sessions
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        sessions = pt.get("sessions", [])
        if not sessions:
            st.info("No ECG sessions recorded for this patient yet.")
        else:
            section_header(f"ECG Session History ({len(sessions)} sessions)")
            for sess in reversed(sessions):
                sr = RISK_STYLE.get(sess.get("risk_level","Unknown"), RISK_STYLE["Unknown"])
                st.markdown(f"""
                <div class="sess-row" style="border-left:3px solid {sr['color']};">
                  <div>
                    <div style="font-weight:700;color:#e2e2e6;">{sess.get('file','?')}</div>
                    <div class="sess-time">{sess.get('timestamp','?')[:16]} · Session {sess.get('session_id','?')}</div>
                    <div style="font-size:.7rem;color:#bac9cc;margin-top:.2rem;">{sess.get('notes','')}</div>
                  </div>
                  <div style="text-align:right;min-width:90px;">
                    <span style="color:{sr['color']};font-weight:700;font-size:.8rem;">{sr['icon']} {sess.get('risk_level','?')}</span><br>
                    <span style="font-size:.68rem;color:#849396;">Score: {sess.get('risk_score',0):.0f}/100</span><br>
                    <span style="font-size:.68rem;color:#c3f400;">HRV: {sess.get('hrv_score',0):.0f}/100</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # Export
        if st.button("📥 Export Patient Record (JSON)", use_container_width=False):
            st.download_button("Download JSON", data=json.dumps(pt, indent=2),
                               file_name=f"patient_{chosen}.json", mime="application/json")

if __name__ == "__main__":
    main()
