"""
Heart Disease Detection Module
===============================
Provides two complementary classifiers:

1. Rule-based classifier  — uses established clinical HRV thresholds
   (SDNN, RMSSD, DFA α1, LF/HF Ratio, Mean HR)

2. ML-based classifier (Random Forest) — trained inline on synthetic
   HRV reference ranges; no external model file required.

Output
------
{
  "risk_level"  : "Normal" | "Mild Risk" | "High Risk",
  "confidence"  : float (0–100),
  "score"       : int (0–100),
  "method"      : "Rule-Based" | "ML-Enhanced",
  "flags"       : { metric_name: {"value", "status", "threshold", "clinical_note"} },
  "explanation" : str,
}
"""

from __future__ import annotations
import math
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Clinical threshold tables
# ─────────────────────────────────────────────────────────────────────────────

THRESHOLDS = {
    "SDNN (ms)": {
        "high_risk": 20,   # < 20 → High
        "mild_risk": 50,   # 20-50 → Mild
        "normal":    50,   # ≥ 50  → Normal
        "direction": "lower_bad",
        "weight": 30,
        "note_high": "Severely reduced HRV — strongly associated with autonomic neuropathy and post-MI risk.",
        "note_mild": "Reduced overall HRV. May indicate autonomic imbalance or cardiovascular stress.",
        "note_normal": "Normal overall HRV — healthy autonomic regulation.",
    },
    "RMSSD (ms)": {
        "high_risk": 10,
        "mild_risk": 20,
        "normal":    20,
        "direction": "lower_bad",
        "weight": 25,
        "note_high": "Very low vagal tone — indicates severe parasympathetic withdrawal.",
        "note_mild": "Reduced vagal tone — mildly elevated sympathetic activity.",
        "note_normal": "Good vagal tone — healthy parasympathetic modulation.",
    },
    "LF/HF Ratio": {
        "high_risk_lo": 0.4,   # < 0.4 → High (extreme parasympathetic dominance)
        "high_risk_hi": 5.0,   # > 5.0 → High (severe sympathetic dominance)
        "mild_risk_lo": 0.7,
        "mild_risk_hi": 3.5,
        "direction": "range",
        "weight": 20,
        "note_high": "Severely imbalanced sympathovagal regulation — cardiac autonomic dysfunction.",
        "note_mild": "Sympathovagal imbalance detected — monitor for arrhythmia risk.",
        "note_normal": "Balanced sympathovagal modulation.",
    },
    "Mean HR (bpm)": {
        "high_risk_lo": 40,    # < 40 → High (bradycardia)
        "high_risk_hi": 130,   # > 130 → High (tachycardia)
        "mild_risk_lo": 50,
        "mild_risk_hi": 110,
        "direction": "range",
        "weight": 15,
        "note_high": "Severe bradycardia or tachycardia — requires urgent clinical evaluation.",
        "note_mild": "Heart rate outside normal resting range — possible arrhythmia.",
        "note_normal": "Normal resting heart rate (60–100 bpm).",
    },
    "DFA α1": {
        "high_risk_lo": 0.5,   # < 0.5 → abnormal (loss of fractal correlation)
        "high_risk_hi": 1.5,   # > 1.5 → Brownian noise (pathological)
        "mild_risk_lo": 0.75,
        "mild_risk_hi": 1.3,
        "direction": "range",
        "weight": 10,
        "note_high": "Loss of fractal correlations — associated with atrial fibrillation and cardiac events.",
        "note_mild": "Slightly abnormal fractal scaling — subtle autonomic dysregulation.",
        "note_normal": "Healthy fractal heart rate dynamics (α1 ≈ 1.0).",
    },
}

# Arrhythmia flags based on ectopic beat rate
ARRHYTHMIA_THRESHOLDS = {
    "high_risk": 15,   # % ectopic beats
    "mild_risk": 5,
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(v) -> float | None:
    """Return float or None; guard NaN / None."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f != f) else f  # NaN → None
    except Exception:
        return None


def _classify_metric(key: str, value: float | None) -> tuple[str, str]:
    """
    Returns (status, note) — status ∈ {'high_risk', 'mild_risk', 'normal', 'unavailable'}.
    """
    if value is None or not math.isfinite(value):
        return "unavailable", "Metric not available — run full HRV pipeline."

    cfg = THRESHOLDS.get(key)
    if cfg is None:
        return "unavailable", "Threshold not defined."

    direction = cfg["direction"]

    if direction == "lower_bad":
        if value < cfg["high_risk"]:
            return "high_risk", cfg["note_high"]
        elif value < cfg["mild_risk"]:
            return "mild_risk", cfg["note_mild"]
        else:
            return "normal", cfg["note_normal"]

    elif direction == "range":
        if value < cfg["high_risk_lo"] or value > cfg["high_risk_hi"]:
            return "high_risk", cfg["note_high"]
        elif value < cfg["mild_risk_lo"] or value > cfg["mild_risk_hi"]:
            return "mild_risk", cfg["note_mild"]
        else:
            return "normal", cfg["note_normal"]

    return "unavailable", "Unknown direction."


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based classifier
# ─────────────────────────────────────────────────────────────────────────────

def classify_cardiovascular_risk_rules(
    metrics: dict,
    pct_ectopic: float = 0.0,
) -> dict:
    """
    Rule-based cardiovascular risk classifier.

    Parameters
    ----------
    metrics     : merged HRV metrics dict (time + freq + nonlinear keys)
    pct_ectopic : % of ectopic beats detected (0–100)

    Returns
    -------
    Classification dict (see module docstring).
    """
    flags = {}
    weighted_score = 0.0
    total_weight   = 0.0

    # Map DFA α1 key variants
    dfa_val = (metrics.get("DFA α1")
               or metrics.get("DFA alpha1")
               or metrics.get("alpha1"))

    lookup = {
        "SDNN (ms)":    metrics.get("SDNN (ms)"),
        "RMSSD (ms)":   metrics.get("RMSSD (ms)"),
        "LF/HF Ratio":  metrics.get("LF/HF Ratio"),
        "Mean HR (bpm)": metrics.get("Mean HR (bpm)"),
        "DFA α1":       dfa_val,
    }

    for key, val in lookup.items():
        cfg    = THRESHOLDS[key]
        fval   = _safe_float(val)
        status, note = _classify_metric(key, fval)

        if status == "unavailable":
            flags[key] = {
                "value": "N/A", "status": "unavailable",
                "threshold": "N/A", "clinical_note": note,
            }
            continue

        weight = cfg["weight"]
        total_weight += weight

        if status == "high_risk":
            contribution = weight * 1.0
        elif status == "mild_risk":
            contribution = weight * 0.5
        else:
            contribution = 0.0

        weighted_score += contribution

        # Build threshold display string
        direction = cfg["direction"]
        if direction == "lower_bad":
            thr_str = (f"High risk < {cfg['high_risk']} | "
                       f"Mild risk < {cfg['mild_risk']}")
        else:
            thr_str = (f"High risk < {cfg['high_risk_lo']} or > {cfg['high_risk_hi']} | "
                       f"Mild risk < {cfg['mild_risk_lo']} or > {cfg['mild_risk_hi']}")

        flags[key] = {
            "value":          f"{fval:.2f}",
            "status":         status,
            "threshold":      thr_str,
            "clinical_note":  note,
        }

    # Arrhythmia contribution
    if pct_ectopic >= ARRHYTHMIA_THRESHOLDS["high_risk"]:
        arr_status = "high_risk"
        arr_note   = f"Ectopic beat rate {pct_ectopic:.1f}% — significant arrhythmia risk (PVC/PAC)."
        total_weight += 15
        weighted_score += 15
    elif pct_ectopic >= ARRHYTHMIA_THRESHOLDS["mild_risk"]:
        arr_status = "mild_risk"
        arr_note   = f"Ectopic beat rate {pct_ectopic:.1f}% — elevated irregularity."
        total_weight += 15
        weighted_score += 7.5
    else:
        arr_status = "normal"
        arr_note   = f"Ectopic beat rate {pct_ectopic:.1f}% — within normal limits."
        total_weight += 15

    flags["Arrhythmia (Ectopic Rate)"] = {
        "value":         f"{pct_ectopic:.1f}%",
        "status":        arr_status,
        "threshold":     f"Mild ≥ {ARRHYTHMIA_THRESHOLDS['mild_risk']}% | High ≥ {ARRHYTHMIA_THRESHOLDS['high_risk']}%",
        "clinical_note": arr_note,
    }

    # Normalise score to 0–100
    score = round(weighted_score / max(total_weight, 1) * 100, 1)

    if score >= 60:
        risk_level = "High Risk"
        confidence = min(score + 15, 98)
    elif score >= 30:
        risk_level = "Mild Risk"
        confidence = min(50 + score * 0.5, 85)
    else:
        risk_level = "Normal"
        confidence = max(80 - score, 55)

    explanation = _build_explanation(risk_level, flags, score)

    return {
        "risk_level":  risk_level,
        "confidence":  round(confidence, 1),
        "score":       score,
        "method":      "Rule-Based",
        "flags":       flags,
        "explanation": explanation,
    }


def _build_explanation(risk_level: str, flags: dict, score: float) -> str:
    """Generate a clinical explanation paragraph."""
    n_high = sum(1 for v in flags.values() if v["status"] == "high_risk")
    n_mild = sum(1 for v in flags.values() if v["status"] == "mild_risk")

    if risk_level == "High Risk":
        intro = (
            f"⚠️ **High Cardiovascular Risk Detected** (risk score: {score:.0f}/100). "
            f"{n_high} indicator(s) exceeded critical thresholds. "
            "Immediate clinical evaluation is strongly recommended."
        )
    elif risk_level == "Mild Risk":
        intro = (
            f"🟡 **Mild Cardiovascular Risk** (risk score: {score:.0f}/100). "
            f"{n_mild} indicator(s) outside normal ranges. "
            "Regular monitoring and lifestyle review are advised."
        )
    else:
        intro = (
            f"✅ **Normal Cardiovascular Profile** (risk score: {score:.0f}/100). "
            "All key HRV indicators are within clinically acceptable ranges. "
            "Continue regular health monitoring."
        )

    high_keys = [k for k, v in flags.items() if v["status"] == "high_risk"]
    mild_keys = [k for k, v in flags.items() if v["status"] == "mild_risk"]

    detail_parts = []
    if high_keys:
        detail_parts.append(f"**Critical flags:** {', '.join(high_keys)}.")
    if mild_keys:
        detail_parts.append(f"**Mild flags:** {', '.join(mild_keys)}.")
    if not high_keys and not mild_keys:
        detail_parts.append("No flags raised across HRV metrics and arrhythmia index.")

    disclaimer = (
        "\n\n*Note: This automated assessment is based on HRV analysis and does not replace "
        "a professional medical diagnosis. Consult a cardiologist for clinical decisions.*"
    )

    return intro + "\n\n" + " ".join(detail_parts) + disclaimer


# ─────────────────────────────────────────────────────────────────────────────
# ML-enhanced classifier (Random Forest, trained inline)
# ─────────────────────────────────────────────────────────────────────────────

def _build_ml_classifier():
    """
    Train a RandomForestClassifier on synthetic HRV reference data.
    Returns a fitted sklearn Pipeline or None if sklearn unavailable.
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        rng = np.random.default_rng(42)

        def _sample(n, sdnn_range, rmssd_range, lf_hf_range, hr_range, dfa_range, label):
            rows = []
            for _ in range(n):
                row = [
                    rng.uniform(*sdnn_range),
                    rng.uniform(*rmssd_range),
                    rng.uniform(*lf_hf_range),
                    rng.uniform(*hr_range),
                    rng.uniform(*dfa_range),
                ]
                rows.append(row)
            return rows, [label] * n

        # Normal
        X_norm, y_norm = _sample(200, (55, 140), (25, 80), (0.8, 2.5), (55, 100), (0.85, 1.25), 0)
        # Mild
        X_mild, y_mild = _sample(200, (22, 55),  (12, 25), (0.5, 4.0), (48, 115), (0.65, 0.84), 1)
        X_mild2, y_mild2 = _sample(100, (22, 55), (12, 25), (2.6, 4.9), (48, 115), (1.26, 1.45), 1)
        # High
        X_high, y_high = _sample(200, (5,  22),  (3,  12), (0.1, 0.4), (30, 48),  (0.3, 0.65), 2)
        X_high2, y_high2 = _sample(100, (5, 22),  (3, 12),  (5.1, 9.0), (120, 180), (1.5, 2.5), 2)

        X = np.array(X_norm + X_mild + X_mild2 + X_high + X_high2)
        y = np.array(y_norm + y_mild + y_mild2 + y_high + y_high2)

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    RandomForestClassifier(
                n_estimators=120, max_depth=8, random_state=42, n_jobs=-1)),
        ])
        pipe.fit(X, y)
        return pipe

    except ImportError:
        return None


_ML_MODEL = None   # lazy singleton

LABEL_MAP = {0: "Normal", 1: "Mild Risk", 2: "High Risk"}


def classify_cardiovascular_risk_ml(metrics: dict) -> dict | None:
    """
    ML-based classifier.  Returns same structure as rule-based classifier,
    or None if sklearn is unavailable or metrics are insufficient.
    """
    global _ML_MODEL

    features = {
        "SDNN (ms)":     _safe_float(metrics.get("SDNN (ms)")),
        "RMSSD (ms)":    _safe_float(metrics.get("RMSSD (ms)")),
        "LF/HF Ratio":   _safe_float(metrics.get("LF/HF Ratio")),
        "Mean HR (bpm)": _safe_float(metrics.get("Mean HR (bpm)")),
        "DFA α1":        _safe_float(
            metrics.get("DFA α1") or metrics.get("DFA alpha1") or metrics.get("alpha1")),
    }

    # Need at least 3 non-null features
    valid_vals = [v for v in features.values() if v is not None]
    if len(valid_vals) < 3:
        return None

    # Fill missing with median-like neutrals
    defaults = {"SDNN (ms)": 70, "RMSSD (ms)": 35, "LF/HF Ratio": 1.5,
                "Mean HR (bpm)": 75, "DFA α1": 1.0}
    X = np.array([[features[k] if features[k] is not None else defaults[k]
                   for k in features]])

    try:
        if _ML_MODEL is None:
            _ML_MODEL = _build_ml_classifier()
        if _ML_MODEL is None:
            return None

        pred    = int(_ML_MODEL.predict(X)[0])
        proba   = _ML_MODEL.predict_proba(X)[0]
        risk    = LABEL_MAP[pred]
        conf    = round(float(proba[pred]) * 100, 1)

        return {
            "risk_level":  risk,
            "confidence":  conf,
            "score":       round((pred / 2) * 100, 1),
            "method":      "ML-Enhanced (Random Forest)",
            "probabilities": {
                "Normal":    round(float(proba[0]) * 100, 1),
                "Mild Risk": round(float(proba[1]) * 100, 1),
                "High Risk": round(float(proba[2]) * 100, 1),
            },
            "flags":       {},   # flags come from rule-based
            "explanation": f"ML model confidence: {conf:.1f}% for **{risk}**.",
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Unified public API
# ─────────────────────────────────────────────────────────────────────────────

def classify_cardiovascular_risk(
    metrics: dict,
    pct_ectopic: float = 0.0,
    use_ml: bool = True,
) -> dict:
    """
    Full cardiovascular risk classification.

    Runs rule-based classifier (always) and optionally ML classifier.
    Returns a merged result with the rule-based flags and the best
    available confidence estimate.

    Parameters
    ----------
    metrics     : merged HRV metrics dict
    pct_ectopic : % ectopic beats (0–100)
    use_ml      : attempt ML classification if sklearn is available

    Returns
    -------
    Classification dict — see module docstring.
    """
    rule = classify_cardiovascular_risk_rules(metrics, pct_ectopic)

    if use_ml:
        ml = classify_cardiovascular_risk_ml(metrics)
        if ml is not None:
            # Blend: rule-based flags + ML confidence when agreement exists
            if ml["risk_level"] == rule["risk_level"]:
                rule["confidence"] = round((rule["confidence"] + ml["confidence"]) / 2, 1)
                rule["method"]     = "Rule-Based + ML-Enhanced"
            rule["ml_result"]  = ml

    return rule
