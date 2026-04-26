"""
R-Peak Detection:
  - Custom Pan-Tompkins from scratch (CLO1 demonstration)
  - NeuroKit2 / Hamilton / Elgendi methods
  - Multi-method comparison and agreement analysis
"""
import numpy as np
import scipy.signal as sig


# ── CUSTOM PAN-TOMPKINS (CLO1) ────────────────────────────────────────────────

def pan_tompkins_detect(ecg: np.ndarray, sfreq: float) -> np.ndarray:
    """
    Complete Pan-Tompkins (1985) R-peak detection implemented from scratch.

    Pipeline
    --------
    1. Bandpass filter  5–15 Hz
    2. Five-point derivative
    3. Point-wise squaring
    4. Moving-window integration  (150 ms)
    5. Adaptive dual-threshold peak classification
    6. Back-projection to original ECG for sub-sample accuracy
    """
    ecg = np.asarray(ecg, dtype=float)
    N = len(ecg)
    if N < 10:
        return np.array([], dtype=int)

    # ── Step 1: Bandpass 5-15 Hz ─────────────────────────────────────────────
    nyq = 0.5 * sfreq
    low  = max(5.0  / nyq, 0.01)
    high = min(15.0 / nyq, 0.99)
    b, a = sig.butter(2, [low, high], btype='band')
    filtered = sig.filtfilt(b, a, ecg)

    # ── Step 2: Derivative (five-point central difference) ───────────────────
    # h(nT) = (1/8T)[-1, -2, 0, 2, 1]
    h = np.array([-1.0, -2.0, 0.0, 2.0, 1.0]) / (8.0 / sfreq)
    differentiated = np.convolve(filtered, h, mode='same')

    # ── Step 3: Squaring ──────────────────────────────────────────────────────
    squared = differentiated ** 2

    # ── Step 4: Moving-window integration  (150 ms) ───────────────────────────
    win_len = max(1, int(0.150 * sfreq))
    mwi = np.convolve(squared, np.ones(win_len) / win_len, mode='same')

    # ── Step 5: Adaptive thresholding ────────────────────────────────────────
    init_end = min(int(2.0 * sfreq), N)
    spk_i = float(np.max(mwi[:init_end]))
    npk_i = float(np.mean(mwi[:init_end]))
    if spk_i < 1e-6:
        spk_i = 1e-6
    thr1  = npk_i + 0.25 * (spk_i - npk_i)
    thr2  = 0.5 * thr1

    min_dist = max(1, int(0.200 * sfreq))           # 200 ms refractory
    candidates, _ = sig.find_peaks(mwi, distance=min_dist)

    qrs_locs = []
    rr_buf   = []
    rr_avg   = int(0.8 * sfreq)

    for peak in candidates:
        amp = mwi[peak]
        if amp >= thr1:
            qrs_locs.append(peak)
            spk_i = 0.125 * amp + 0.875 * spk_i
            if len(qrs_locs) > 1:
                rr_buf.append(qrs_locs[-1] - qrs_locs[-2])
                rr_avg = int(np.mean(rr_buf[-8:]))
        elif amp >= thr2:
            # Searchback: accept if last beat was >1.66 × average RR ago
            if qrs_locs and (peak - qrs_locs[-1]) > 1.66 * rr_avg:
                qrs_locs.append(peak)
                spk_i = 0.25 * amp + 0.875 * spk_i
            else:
                npk_i = 0.125 * amp + 0.875 * npk_i
        else:
            npk_i = 0.125 * amp + 0.875 * npk_i

        thr1 = npk_i + 0.25 * (spk_i - npk_i)
        thr2 = 0.5 * thr1

    if not qrs_locs:
        return np.array([], dtype=int)

    # ── Step 6: Back-project to raw ECG within ±50 ms ─────────────────────────
    win = max(1, int(0.05 * sfreq))
    refined = []
    for q in qrs_locs:
        s = max(0, q - win)
        e = min(N, q + win)
        refined.append(int(np.argmax(np.abs(ecg[s:e])) + s))

    refined = sorted(set(refined))
    final = [refined[0]]
    for r in refined[1:]:
        if r - final[-1] >= min_dist:
            final.append(r)

    return np.array(final, dtype=int)


# ── DISPATCHER ────────────────────────────────────────────────────────────────

def detect_r_peaks(ecg_cleaned: np.ndarray, sfreq: float,
                   method: str = 'NeuroKit') -> np.ndarray:
    """
    Detect R-peaks using the requested method.
    Returns integer array of sample indices.
    """
    if method == "Pan-Tompkins (Custom)":
        return pan_tompkins_detect(ecg_cleaned, sfreq)

    import neurokit2 as nk
    method_map = {
        "NeuroKit":     "neurokit",
        "Pan-Tompkins": "pantompkins1985",
        "Hamilton":     "hamilton2002",
        "Elgendi":      "elgendi2010",
        "Rodrigues":    "rodrigues2021",
    }
    nk_method = method_map.get(method, "neurokit")
    try:
        _, rd = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(sfreq), method=nk_method)
        return rd['ECG_R_Peaks'].astype(int)
    except Exception:
        _, rd = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(sfreq))
        return rd['ECG_R_Peaks'].astype(int)


# ── MULTI-METHOD COMPARISON ───────────────────────────────────────────────────

def compare_r_peak_methods(ecg: np.ndarray, sfreq: float,
                           methods: list = None) -> dict:
    """
    Run several detection methods and return results dict.

    Returns
    -------
    {method_name: {"rpeaks": ndarray, "count": int, "mean_hr": float}}
    """
    if methods is None:
        methods = ["Pan-Tompkins (Custom)", "NeuroKit", "Pan-Tompkins", "Hamilton"]
    results = {}
    for m in methods:
        try:
            rp = detect_r_peaks(ecg, sfreq, method=m)
            hr = (60000.0 / float(np.mean(np.diff(rp) / sfreq * 1000))
                  if len(rp) >= 2 else 0.0)
            results[m] = {"rpeaks": rp, "count": int(len(rp)),
                          "mean_hr": round(hr, 1)}
        except Exception as exc:
            results[m] = {"rpeaks": np.array([], dtype=int),
                          "count": 0, "mean_hr": 0.0, "error": str(exc)}
    return results


def compute_agreement(rpeaks_a: np.ndarray, rpeaks_b: np.ndarray,
                      tolerance_ms: float = 50.0, sfreq: float = 250.0) -> float:
    """
    Percentage agreement between two R-peak sets within ± tolerance_ms.
    """
    if len(rpeaks_a) == 0 or len(rpeaks_b) == 0:
        return 0.0
    tol = int(tolerance_ms / 1000.0 * sfreq)
    matches = sum(1 for r in rpeaks_a if np.any(np.abs(rpeaks_b - r) <= tol))
    return round(100.0 * matches / max(len(rpeaks_a), len(rpeaks_b)), 1)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_rr_intervals(rpeaks: np.ndarray, sfreq: float) -> np.ndarray:
    """RR intervals in milliseconds."""
    if len(rpeaks) < 2:
        return np.array([])
    return np.diff(rpeaks.astype(float)) / sfreq * 1000.0


def compute_heart_rate(rpeaks: np.ndarray, sfreq: float) -> float:
    """Mean heart rate in BPM."""
    if len(rpeaks) < 2:
        return 0.0
    rr = get_rr_intervals(rpeaks, sfreq)
    return 60000.0 / float(np.mean(rr)) if float(np.mean(rr)) > 0 else 0.0
