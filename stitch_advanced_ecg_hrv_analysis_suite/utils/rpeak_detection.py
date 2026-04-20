import neurokit2 as nk
import numpy as np
import pandas as pd

def detect_r_peaks(ecg_cleaned: np.ndarray, sfreq: float, method: str = 'neurokit'):
    """
    Detects R-peaks in the cleaned ECG signal.
    Returns:
        rpeaks: dict containing 'ECG_R_Peaks': array of sample indices
    """
    try:
        # We can support different methods
        # options: "pantompkins1985", "neurokit", "hamilton2002", etc.
        method_map = {
            "Pan-Tompkins": "pantompkins1985",
            "NeuroKit": "neurokit",
            "Hamilton": "hamilton2002"
        }
        nk_method = method_map.get(method, "neurokit")
        _, rpeaks = nk.ecg_peaks(ecg_cleaned, sampling_rate=int(sfreq), method=nk_method)
        return rpeaks['ECG_R_Peaks']
    except Exception as e:
        raise RuntimeError(f"Peak detection failed using method {method}: {e}")

def get_rr_intervals(rpeaks_indices: np.ndarray, sfreq: float):
    """
    Calculates RR intervals from R-peak indices.
    Returns:
        rr_intervals: array of RR intervals in milliseconds.
    """
    rr_intervals_sec = np.diff(rpeaks_indices) / sfreq
    rr_intervals_ms = rr_intervals_sec * 1000.0
    return rr_intervals_ms
