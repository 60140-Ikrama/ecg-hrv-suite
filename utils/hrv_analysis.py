"""
HRV Analysis:
  - Ectopic beat detection (median / mean / combined) and correction
  - Anomaly detection (z-score, clinical labelling)
  - Time-domain metrics
  - Frequency-domain (Welch PSD, configurable)
  - Non-linear: Poincaré (SD1/SD2), Sample Entropy, Approximate Entropy
  - Detrended Fluctuation Analysis (DFA) — α1 & α2
  - HRV trend analysis (sliding-window)
  - Clinical interpretation
"""
import math
import numpy as np
import pandas as pd
import scipy.signal as sig
from scipy.interpolate import interp1d


# ── ECTOPIC BEAT HANDLING ─────────────────────────────────────────────────────

def detect_ectopic_beats(rr_ms: np.ndarray,
                         threshold: float = 0.20,
                         method: str = "median") -> np.ndarray:
    """
    Multi-method ectopic detection.

    method : 'median' | 'mean' | 'combined'
    Returns boolean mask (True = ectopic).
    """
    if len(rr_ms) < 5:
        return np.zeros(len(rr_ms), dtype=bool)

    s = pd.Series(rr_ms)
    med = s.rolling(5, center=True, min_periods=1).median().values
    mn  = s.rolling(5, center=True, min_periods=1).mean().values

    dev_med  = np.abs(rr_ms - med) / (med + 1e-9)
    dev_mean = np.abs(rr_ms - mn)  / (mn  + 1e-9)

    if method == "median":
        return dev_med > threshold
    elif method == "mean":
        return dev_mean > threshold
    else:                                     # combined
        return (dev_med > threshold) | (dev_mean > threshold)


def correct_ectopic_beats(rr_ms: np.ndarray, mask: np.ndarray,
                          method: str = "Linear") -> np.ndarray:
    """Interpolate over ectopic-flagged beats (Linear or Cubic Spline)."""
    clean = rr_ms.copy()
    if not np.any(mask):
        return clean
    valid = np.where(~mask)[0]
    if len(valid) < 2:
        return clean
    bad = np.where(mask)[0]
    kind = 'cubic' if method == "Spline" and len(valid) > 3 else 'linear'
    try:
        f = interp1d(valid, clean[valid], kind=kind, fill_value="extrapolate")
        clean[bad] = f(bad)
    except Exception:
        f = interp1d(valid, clean[valid], kind='linear', fill_value="extrapolate")
        clean[bad] = f(bad)
    return clean


# ── ANOMALY DETECTION ─────────────────────────────────────────────────────────

def detect_anomalies(rr_ms: np.ndarray, z_threshold: float = 3.0) -> dict:
    """
    Z-score anomaly detector with clinical classification.

    Returns
    -------
    {"indices": list[int], "types": list[str], "z_scores": ndarray}
    """
    if len(rr_ms) < 5:
        return {"indices": [], "types": [], "z_scores": np.array([])}
    mu, sd = float(np.mean(rr_ms)), float(np.std(rr_ms, ddof=1))
    z = (rr_ms - mu) / (sd + 1e-9)
    idx = np.where(np.abs(z) > z_threshold)[0]
    types = ["Short RR (Tachycardia risk)" if z[i] < 0 else
             "Long RR (Bradycardia / ectopic risk)" for i in idx]
    return {"indices": idx.tolist(), "types": types, "z_scores": z}


# ── TIME-DOMAIN HRV ───────────────────────────────────────────────────────────

def get_time_domain_hrv(rr_ms: np.ndarray) -> dict:
    """Standard time-domain HRV metrics."""
    if len(rr_ms) < 3:
        return {}
    diff = np.diff(rr_ms)
    return {
        "Mean RR (ms)":   round(float(np.mean(rr_ms)), 2),
        "SDNN (ms)":      round(float(np.std(rr_ms, ddof=1)), 2),
        "RMSSD (ms)":     round(float(np.sqrt(np.mean(diff**2))), 2),
        "NN50":           int(np.sum(np.abs(diff) > 50)),
        "pNN50 (%)":      round(float(np.sum(np.abs(diff) > 50) / max(len(diff), 1) * 100), 2),
        "Mean HR (bpm)":  round(60000.0 / float(np.mean(rr_ms)), 1),
        "SDSD (ms)":      round(float(np.std(diff, ddof=1)), 2),
        "CV (%)":         round(float(np.std(rr_ms, ddof=1) / np.mean(rr_ms) * 100), 2),
    }


# ── FREQUENCY-DOMAIN HRV ──────────────────────────────────────────────────────

def get_freq_domain_hrv(rr_ms: np.ndarray,
                        vlf_band: tuple = (0.003, 0.04),
                        lf_band:  tuple = (0.04,  0.15),
                        hf_band:  tuple = (0.15,  0.40),
                        fs_resample: float = 4.0,
                        nperseg: int = 256,
                        noverlap: int = None):
    """
    Welch PSD with configurable segmenting.

    Returns (metrics_dict, freqs, psd)  — or (None, None, None) on failure.
    """
    if len(rr_ms) < 10:
        return None, None, None

    t = np.cumsum(rr_ms) / 1000.0
    t -= t[0]
    t_uni = np.arange(0, t[-1], 1.0 / fs_resample)
    if len(t_uni) < 64:
        return None, None, None

    try:
        rr_uni = interp1d(t, rr_ms, kind='cubic', fill_value='extrapolate')(t_uni)
    except Exception:
        return None, None, None

    nperseg  = min(nperseg, len(rr_uni) // 2)
    noverlap = noverlap if noverlap is not None else nperseg // 2
    noverlap = min(noverlap, nperseg - 1)

    freqs, psd = sig.welch(rr_uni, fs=fs_resample,
                           nperseg=nperseg, noverlap=noverlap,
                           scaling='density')

    def _bp(fmin, fmax):
        idx = (freqs >= fmin) & (freqs < fmax)
        if np.sum(idx) > 1:
            try:
                return float(np.trapezoid(psd[idx], freqs[idx]))
            except AttributeError:
                return float(np.trapz(psd[idx], freqs[idx]))
        return 0.0

    vlf   = _bp(*vlf_band)
    lf    = _bp(*lf_band)
    hf    = _bp(*hf_band)
    total = vlf + lf + hf

    metrics = {
        "VLF Power (ms²)": round(vlf, 2),
        "LF Power (ms²)":  round(lf,  2),
        "HF Power (ms²)":  round(hf,  2),
        "LF/HF Ratio":     round(lf / hf, 3) if hf > 0 else float('nan'),
        "Total Power (ms²)": round(total, 2),
        "LF norm (%)":     round(lf / (lf + hf) * 100, 1) if (lf + hf) > 0 else 0.0,
        "HF norm (%)":     round(hf / (lf + hf) * 100, 1) if (lf + hf) > 0 else 0.0,
    }
    return metrics, freqs, psd


# ── NON-LINEAR HRV ────────────────────────────────────────────────────────────

def get_nonlinear_hrv(rr_ms: np.ndarray) -> dict:
    """Poincaré SD1, SD2, ellipse area, and SD1/SD2 ratio."""
    if len(rr_ms) < 2:
        return {}
    d = np.diff(rr_ms)
    sd1 = float(np.std(d / np.sqrt(2), ddof=1))
    sd2 = float(np.std((rr_ms[:-1] + rr_ms[1:]) / np.sqrt(2), ddof=1))
    return {
        "SD1 (ms)":           round(sd1, 2),
        "SD2 (ms)":           round(sd2, 2),
        "SD1/SD2":            round(sd1 / sd2, 3) if sd2 > 0 else float('nan'),
        "Ellipse Area (ms²)": round(math.pi * sd1 * sd2, 2),
    }


def sample_entropy(rr_ms: np.ndarray, m: int = 2,
                   r_factor: float = 0.2) -> float:
    """Sample Entropy (SampEn). O(N²) — limit input to ≤300 points."""
    N = len(rr_ms)
    if N < 2 * m + 1:
        return float('nan')
    r = r_factor * float(np.std(rr_ms, ddof=1))

    def _count(tlen):
        cnt = 0
        for i in range(N - tlen):
            for j in range(i + 1, N - tlen):
                if np.max(np.abs(rr_ms[i:i+tlen] - rr_ms[j:j+tlen])) < r:
                    cnt += 1
        return cnt

    B = _count(m)
    A = _count(m + 1)
    if B == 0:
        return float('nan')
    return float(-np.log(A / B)) if A > 0 else float('inf')


def approximate_entropy(rr_ms: np.ndarray, m: int = 2,
                        r_factor: float = 0.2) -> float:
    """Approximate Entropy (ApEn)."""
    N = len(rr_ms)
    if N < m + 2:
        return float('nan')
    r = r_factor * float(np.std(rr_ms, ddof=1))

    def _phi(tlen):
        cnt = np.array([
            np.sum([
                np.max(np.abs(rr_ms[i:i+tlen] - rr_ms[j:j+tlen])) < r
                for j in range(N - tlen + 1)
            ])
            for i in range(N - tlen + 1)
        ], dtype=float)
        cnt = np.maximum(cnt, 1)
        return float(np.mean(np.log(cnt / (N - tlen + 1))))

    try:
        return float(_phi(m) - _phi(m + 1))
    except Exception:
        return float('nan')


# ── DETRENDED FLUCTUATION ANALYSIS ───────────────────────────────────────────

def detrended_fluctuation_analysis(rr_ms: np.ndarray,
                                   min_box: int = 4,
                                   max_box_ratio: float = 0.5) -> dict:
    """
    DFA — computes short-term (α1, 4–16 beats) and long-term (α2, 16–64 beats)
    scaling exponents.

    Returns
    -------
    {"alpha1": float, "alpha2": float, "scales": array, "fluct": array}
    """
    N = len(rr_ms)
    if N < 32:
        return {"alpha1": float('nan'), "alpha2": float('nan'),
                "scales": np.array([]), "fluct": np.array([])}

    # Integrate (cumulative sum minus mean)
    y = np.cumsum(rr_ms - np.mean(rr_ms))

    max_box = max(min_box + 1, int(N * max_box_ratio))
    scales  = np.unique(np.logspace(np.log10(min_box),
                                    np.log10(max_box), 20).astype(int))
    fluct   = []

    for n in scales:
        n = int(n)
        n_segs = N // n
        if n_segs < 1:
            fluct.append(np.nan)
            continue
        rms_vals = []
        for k in range(n_segs):
            seg = y[k*n:(k+1)*n]
            x   = np.arange(len(seg))
            coeffs = np.polyfit(x, seg, 1)
            trend  = np.polyval(coeffs, x)
            rms_vals.append(float(np.sqrt(np.mean((seg - trend)**2))))
        fluct.append(float(np.mean(rms_vals)))

    scales = np.array(scales, dtype=float)
    fluct  = np.array(fluct,  dtype=float)
    valid  = np.isfinite(fluct) & (fluct > 0)

    def _alpha(s_mask):
        if np.sum(s_mask) < 2:
            return float('nan')
        lx, ly = np.log10(scales[s_mask]), np.log10(fluct[s_mask])
        c = np.polyfit(lx, ly, 1)
        return round(float(c[0]), 3)

    a1_mask = valid & (scales >= 4)  & (scales <= 16)
    a2_mask = valid & (scales >= 16) & (scales <= 64)

    return {
        "alpha1": _alpha(a1_mask),
        "alpha2": _alpha(a2_mask),
        "scales": scales[valid],
        "fluct":  fluct[valid],
    }


# ── HRV TREND ANALYSIS ────────────────────────────────────────────────────────

def analyze_hrv_trend(rr_ms: np.ndarray,
                      window_beats: int = 60,
                      step_beats: int = 20) -> dict:
    """
    Sliding-window time-domain HRV trend.

    Returns
    -------
    {"beat_centers": array, "sdnn": array, "rmssd": array, "mean_hr": array}
    """
    N = len(rr_ms)
    if N < window_beats:
        return {"beat_centers": np.array([]), "sdnn": np.array([]),
                "rmssd": np.array([]), "mean_hr": np.array([])}

    centers, sdnn_t, rmssd_t, hr_t = [], [], [], []
    for start in range(0, N - window_beats + 1, step_beats):
        w = rr_ms[start:start + window_beats]
        centers.append(start + window_beats // 2)
        sdnn_t.append(float(np.std(w, ddof=1)))
        rmssd_t.append(float(np.sqrt(np.mean(np.diff(w)**2))))
        hr_t.append(float(60000.0 / np.mean(w)))

    return {
        "beat_centers": np.array(centers),
        "sdnn":         np.array(sdnn_t),
        "rmssd":        np.array(rmssd_t),
        "mean_hr":      np.array(hr_t),
    }


# ── CLINICAL INTERPRETATION ───────────────────────────────────────────────────

def interpret_hrv(time_metrics: dict, freq_metrics: dict) -> dict:
    """Generate clinical interpretation strings."""
    interp = {}
    sdnn  = time_metrics.get("SDNN (ms)",  0) or 0
    rmssd = time_metrics.get("RMSSD (ms)", 0) or 0
    lf_hf = (freq_metrics or {}).get("LF/HF Ratio", float('nan'))

    if sdnn > 100:
        interp["sdnn_class"] = "Excellent cardiac autonomic function (SDNN > 100 ms)."
    elif sdnn > 50:
        interp["sdnn_class"] = "Normal cardiac autonomic function (50–100 ms)."
    else:
        interp["sdnn_class"] = "Reduced HRV — potential autonomic dysfunction (SDNN < 50 ms)."

    if math.isnan(lf_hf):
        interp["lf_hf_class"] = "Frequency-domain data unavailable."
    elif lf_hf > 2.0:
        interp["lf_hf_class"] = (f"LF/HF = {lf_hf:.2f} → Sympathetic dominance. "
                                  "Indicates stress, exercise, or upright posture.")
    elif lf_hf < 1.0:
        interp["lf_hf_class"] = (f"LF/HF = {lf_hf:.2f} → Parasympathetic dominance. "
                                  "Associated with rest, recovery, or supine posture.")
    else:
        interp["lf_hf_class"] = (f"LF/HF = {lf_hf:.2f} → Balanced sympathovagal modulation.")

    if rmssd > 40:
        interp["autonomic"] = "High vagal tone — excellent recovery capacity."
    elif rmssd > 20:
        interp["autonomic"] = "Moderate vagal tone — typical resting state."
    else:
        interp["autonomic"] = "Low vagal tone — elevated sympathetic activity."

    return interp
