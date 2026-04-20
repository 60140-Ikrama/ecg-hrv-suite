"""
HRV Analysis: Ectopic removal, time-domain, frequency-domain, and non-linear metrics.
"""
import numpy as np
import pandas as pd
import scipy.signal as sig
from scipy.interpolate import interp1d


# ── ECTOPIC BEAT HANDLING ──────────────────────────────────────────────────────

def detect_ectopic_beats(rr_ms: np.ndarray, threshold: float = 0.20) -> np.ndarray:
    """
    Detect ectopic beats using a moving-median deviation rule.
    Returns boolean mask: True = ectopic.
    """
    if len(rr_ms) < 5:
        return np.zeros(len(rr_ms), dtype=bool)
    series = pd.Series(rr_ms)
    rolling_median = series.rolling(window=5, center=True, min_periods=1).median()
    deviation = np.abs(series.values - rolling_median.values) / rolling_median.values
    return deviation > threshold


def correct_ectopic_beats(rr_ms: np.ndarray, mask: np.ndarray, method: str = "Linear") -> np.ndarray:
    """
    Interpolate over ectopic-flagged beats.
    method: "Linear" | "Spline"
    """
    clean = rr_ms.copy()
    if not np.any(mask):
        return clean
    valid_idx = np.where(~mask)[0]
    if len(valid_idx) < 2:
        return clean
    ectopic_idx = np.where(mask)[0]
    try:
        kind = 'cubic' if method == "Spline" and len(valid_idx) > 3 else 'linear'
        f = interp1d(valid_idx, clean[valid_idx], kind=kind, fill_value="extrapolate")
        clean[ectopic_idx] = f(ectopic_idx)
    except Exception:
        f = interp1d(valid_idx, clean[valid_idx], kind='linear', fill_value="extrapolate")
        clean[ectopic_idx] = f(ectopic_idx)
    return clean


# ── TIME-DOMAIN HRV ───────────────────────────────────────────────────────────

def get_time_domain_hrv(rr_ms: np.ndarray) -> dict:
    """Compute standard time-domain HRV metrics."""
    if len(rr_ms) < 3:
        return {}
    mean_rr = float(np.mean(rr_ms))
    sdnn = float(np.std(rr_ms, ddof=1))
    diff_rr = np.diff(rr_ms)
    rmssd = float(np.sqrt(np.mean(diff_rr ** 2)))
    nn50 = int(np.sum(np.abs(diff_rr) > 50))
    pnn50 = float(nn50 / len(diff_rr) * 100) if len(diff_rr) > 0 else 0.0
    mean_hr = float(60000.0 / mean_rr) if mean_rr > 0 else 0.0
    return {
        "Mean RR (ms)": round(mean_rr, 2),
        "SDNN (ms)": round(sdnn, 2),
        "RMSSD (ms)": round(rmssd, 2),
        "NN50": nn50,
        "pNN50 (%)": round(pnn50, 2),
        "Mean HR (bpm)": round(mean_hr, 1),
    }


# ── FREQUENCY-DOMAIN HRV ──────────────────────────────────────────────────────

def get_freq_domain_hrv(rr_ms: np.ndarray,
                         vlf_band: tuple = (0.003, 0.04),
                         lf_band: tuple = (0.04, 0.15),
                         hf_band: tuple = (0.15, 0.40),
                         fs_resample: float = 4.0):
    """
    Compute Welch PSD and band powers. Resamples the irregularly-spaced
    RR tachogram to a uniform grid at fs_resample Hz.
    Returns: (metrics_dict, freqs_array, psd_array)
    """
    if len(rr_ms) < 10:
        return None, None, None

    # Build time axis (cumulative sum in seconds)
    t = np.cumsum(rr_ms) / 1000.0
    t -= t[0]

    t_uniform = np.arange(0, t[-1], 1.0 / fs_resample)
    if len(t_uniform) < 64:
        return None, None, None

    try:
        f_interp = interp1d(t, rr_ms, kind='cubic', fill_value="extrapolate")
        rr_uniform = f_interp(t_uniform)
    except Exception:
        return None, None, None

    nperseg = min(256, len(rr_uniform) // 2)
    freqs, psd = sig.welch(rr_uniform, fs=fs_resample, nperseg=nperseg, scaling='density')

    def band_power(fmin, fmax):
        idx = np.logical_and(freqs >= fmin, freqs < fmax)
        if np.sum(idx) > 1:
            try:
                return float(np.trapezoid(psd[idx], freqs[idx]))
            except AttributeError:
                return float(np.trapz(psd[idx], freqs[idx]))
        return 0.0

    vlf = band_power(*vlf_band)
    lf = band_power(*lf_band)
    hf = band_power(*hf_band)
    total = vlf + lf + hf

    metrics = {
        "VLF Power (ms²)": round(vlf, 2),
        "LF Power (ms²)": round(lf, 2),
        "HF Power (ms²)": round(hf, 2),
        "LF/HF Ratio": round(lf / hf, 3) if hf > 0 else float('nan'),
        "Total Power (ms²)": round(total, 2),
        "LF norm (%)": round(lf / (lf + hf) * 100, 1) if (lf + hf) > 0 else 0.0,
        "HF norm (%)": round(hf / (lf + hf) * 100, 1) if (lf + hf) > 0 else 0.0,
    }
    return metrics, freqs, psd


# ── NON-LINEAR HRV ────────────────────────────────────────────────────────────

def get_nonlinear_hrv(rr_ms: np.ndarray) -> dict:
    """Compute Poincaré SD1, SD2 and ratio."""
    if len(rr_ms) < 2:
        return {}
    rr_n = rr_ms[:-1]
    rr_n1 = rr_ms[1:]
    sd1 = float(np.std((rr_n - rr_n1) / np.sqrt(2), ddof=1))
    sd2 = float(np.std((rr_n + rr_n1) / np.sqrt(2), ddof=1))
    return {
        "SD1 (ms)": round(sd1, 2),
        "SD2 (ms)": round(sd2, 2),
        "SD1/SD2": round(sd1 / sd2, 3) if sd2 > 0 else float('nan'),
        "Ellipse Area (ms²)": round(np.pi * sd1 * sd2, 2),
    }


def interpret_hrv(time_metrics: dict, freq_metrics: dict) -> dict:
    """
    Generate clinical interpretation strings for the report.
    Returns dict with keys: 'autonomic', 'sdnn_class', 'lf_hf_class'
    """
    interpretation = {}
    sdnn = time_metrics.get("SDNN (ms)", 0)
    rmssd = time_metrics.get("RMSSD (ms)", 0)
    lf_hf = freq_metrics.get("LF/HF Ratio", float('nan')) if freq_metrics else float('nan')

    # SDNN classification
    if sdnn > 100:
        interpretation["sdnn_class"] = "Excellent cardiac autonomic function (SDNN > 100 ms)."
    elif sdnn > 50:
        interpretation["sdnn_class"] = "Normal cardiac autonomic function (50–100 ms range)."
    else:
        interpretation["sdnn_class"] = "Reduced HRV: potential autonomic dysfunction (SDNN < 50 ms)."

    # LF/HF interpretation
    import math
    if math.isnan(lf_hf):
        interpretation["lf_hf_class"] = "Frequency-domain data unavailable."
    elif lf_hf > 2.0:
        interpretation["lf_hf_class"] = (
            f"LF/HF = {lf_hf:.2f} → Sympathetic dominance detected. "
            "May indicate mental or physiological stress, exercise, or standing posture."
        )
    elif lf_hf < 1.0:
        interpretation["lf_hf_class"] = (
            f"LF/HF = {lf_hf:.2f} → Parasympathetic dominance (vagal tone). "
            "Associated with rest, recovery, or supine posture."
        )
    else:
        interpretation["lf_hf_class"] = (
            f"LF/HF = {lf_hf:.2f} → Balanced sympathovagal modulation. "
            "Typical of normal resting state."
        )

    # RMSSD (short-term vagal activity)
    if rmssd > 40:
        interpretation["autonomic"] = "High vagal (parasympathetic) tone: good recovery capacity."
    elif rmssd > 20:
        interpretation["autonomic"] = "Moderate vagal tone: typical resting state."
    else:
        interpretation["autonomic"] = "Low vagal tone: elevated sympathetic activity or poor HRV."

    return interpretation
