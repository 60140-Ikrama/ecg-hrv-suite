"""
Patient Database — JSON file-based persistence for Clinical Sentinel v3.
Provides CRUD operations for patient profiles and ECG session history.
"""
import json
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "patient_data.json")


def _load_db() -> dict:
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"patients": {}}


def _save_db(db: dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def load_patients() -> dict:
    return _load_db().get("patients", {})


def save_patient(patient: dict) -> str:
    db = _load_db()
    pid = patient.get("id") or str(uuid.uuid4())[:8].upper()
    patient["id"] = pid
    patient.setdefault("created_at", datetime.now().isoformat())
    patient["updated_at"] = datetime.now().isoformat()
    patient.setdefault("sessions", [])
    patient.setdefault("risk_level", "Unknown")
    patient.setdefault("tags", [])
    db["patients"][pid] = patient
    _save_db(db)
    return pid


def delete_patient(pid: str):
    db = _load_db()
    db["patients"].pop(pid, None)
    _save_db(db)


def get_patient(pid: str) -> dict:
    return _load_db()["patients"].get(pid, {})


def add_session(pid: str, session: dict):
    db = _load_db()
    if pid not in db["patients"]:
        return
    session.setdefault("timestamp", datetime.now().isoformat())
    session.setdefault("session_id", str(uuid.uuid4())[:8].upper())
    db["patients"][pid]["sessions"].append(session)
    db["patients"][pid]["updated_at"] = datetime.now().isoformat()
    _save_db(db)


def update_patient_risk(pid: str, risk_level: str, risk_score: float):
    db = _load_db()
    if pid in db["patients"]:
        db["patients"][pid]["risk_level"] = risk_level
        db["patients"][pid]["risk_score"] = risk_score
        db["patients"][pid]["updated_at"] = datetime.now().isoformat()
        _save_db(db)


def search_patients(query: str = "", risk_filter: str = "All") -> list:
    patients = load_patients()
    results = []
    for pid, p in patients.items():
        name = p.get("name", "").lower()
        if query and query.lower() not in name and query.lower() not in pid.lower():
            continue
        if risk_filter != "All" and p.get("risk_level", "") != risk_filter:
            continue
        results.append(p)
    return sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True)


def get_demo_patients() -> list:
    return [
        {"id": "PT001", "name": "Ahmad Raza", "age": 58, "sex": "Male",
         "conditions": ["Hypertension", "Type 2 Diabetes"], "medications": ["Metoprolol 50mg", "Metformin 500mg"],
         "risk_level": "High Risk", "risk_score": 72, "tags": ["URGENT"],
         "created_at": "2026-05-01T08:00:00", "updated_at": "2026-05-22T10:30:00",
         "sessions": [
             {"session_id": "S001", "timestamp": "2026-05-22T09:15:00", "file": "ecgpvc.dat",
              "risk_level": "High Risk", "risk_score": 72, "hrv_score": 38,
              "notes": "PVC episodes detected. Refer to cardiologist."}
         ]},
        {"id": "PT002", "name": "Fatima Sheikh", "age": 34, "sex": "Female",
         "conditions": ["Anxiety Disorder"], "medications": ["Propranolol 10mg"],
         "risk_level": "Mild Risk", "risk_score": 41, "tags": [],
         "created_at": "2026-05-10T11:00:00", "updated_at": "2026-05-20T14:00:00",
         "sessions": [
             {"session_id": "S002", "timestamp": "2026-05-20T13:45:00", "file": "ecg_hfn.dat",
              "risk_level": "Mild Risk", "risk_score": 41, "hrv_score": 62,
              "notes": "Elevated LF/HF. Stress-related autonomic imbalance suspected."}
         ]},
        {"id": "PT003", "name": "Bilal Tariq", "age": 27, "sex": "Male",
         "conditions": [], "medications": [],
         "risk_level": "Normal", "risk_score": 12, "tags": ["ATHLETE"],
         "created_at": "2026-05-15T09:00:00", "updated_at": "2026-05-21T16:00:00",
         "sessions": [
             {"session_id": "S003", "timestamp": "2026-05-21T15:30:00", "file": "ecg_lfn.dat",
              "risk_level": "Normal", "risk_score": 12, "hrv_score": 91,
              "notes": "Excellent HRV. Athletic profile confirmed."}
         ]},
    ]
