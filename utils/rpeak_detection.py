"""
R-Peak detection using NeuroKit2 (Pan-Tompkins, Hamilton, NeuroKit methods).
"""
import numpy as np


def detect_r_peaks(ecg_cleaned: np.ndarray, sfreq: float, method: str = 'NeuroKit') -> np.ndarray:
    """
    Detect R-peaks using NeuroKit2.
    Returns array of sample indices for each R-peak.
    """
    import neurokit2 as nk
    method_map = {
        "NeuroKit": "neurokit",
        "Pan-Tompkins": "pantompkins1985",
        "Hamilton": "hamilton2002",
        "Elgendi": "elgendi2010",
        "Rodrigues": "rodrigues2021",
    }
    nk_method = method_map.get(method, "neurokit")
    _, rpeaks_dict = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(sfreq), method=nk_method)
    rpeaks = rpeaks_dict['ECG_R_Peaks']
    return rpeaks.astype(int)


def get_rr_intervals(rpeaks: np.ndarray, sfreq: float) -> np.ndarray:
    """Return RR intervals in milliseconds from R-peak sample indices."""
    if len(rpeaks) < 2:
        return np.array([])
    rr_sec = np.diff(rpeaks.astype(float)) / sfreq
    return rr_sec * 1000.0


def compute_heart_rate(rpeaks: np.ndarray, sfreq: float) -> float:
    """Compute mean heart rate in BPM."""
    if len(rpeaks) < 2:
        return 0.0
    rr_ms = get_rr_intervals(rpeaks, sfreq)
    return 60000.0 / np.mean(rr_ms) if np.mean(rr_ms) > 0 else 0.0
