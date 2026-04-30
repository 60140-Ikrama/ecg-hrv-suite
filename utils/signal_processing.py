"""
Signal Processing: Adaptive bandpass, baseline removal, noise filtering,
powerline suppression, wavelet denoising, and Signal Quality Index (SQI).
"""
import numpy as np
import scipy.signal as sig


# ── INDIVIDUAL FILTER STAGES ──────────────────────────────────────────────────

def apply_bandpass_filter(signal: np.ndarray, sfreq: float,
                          lowcut: float = 0.5, highcut: float = 40.0,
                          order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth bandpass filter."""
    nyq = 0.5 * sfreq
    low = max(lowcut / nyq, 0.001)
    high = min(highcut / nyq, 0.999)
    if low >= high:
        high = min(low + 0.01, 0.999)
    b, a = sig.butter(order, [low, high], btype='band')
    return sig.filtfilt(b, a, signal)


def remove_baseline_wander(signal: np.ndarray, sfreq: float,
                           cutoff: float = 0.5) -> np.ndarray:
    """High-pass Butterworth filter to remove baseline wander."""
    nyq = 0.5 * sfreq
    c = max(min(cutoff / nyq, 0.999), 0.001)
    b, a = sig.butter(4, c, btype='high')
    return sig.filtfilt(b, a, signal)


def apply_notch_filter(signal: np.ndarray, sfreq: float,
                       freq: float = 50.0, Q: float = 30.0) -> np.ndarray:
    """Notch filter for powerline interference."""
    if freq >= 0.5 * sfreq:
        return signal
    b, a = sig.iirnotch(freq / (0.5 * sfreq), Q)
    return sig.filtfilt(b, a, signal)


def apply_wavelet_denoise(signal: np.ndarray, wavelet: str = 'db4',
                          level: int = 4) -> np.ndarray:
    """Wavelet soft-thresholding denoising."""
    try:
        import pywt
        coeffs = pywt.wavedec(signal, wavelet, level=level)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        uthresh = sigma * np.sqrt(2 * np.log(max(len(signal), 1)))
        coeffs[1:] = [pywt.threshold(c, value=uthresh, mode='soft')
                      for c in coeffs[1:]]
        denoised = pywt.waverec(coeffs, wavelet)
        return denoised[:len(signal)]
    except ImportError:
        return signal


def apply_adaptive_filter(signal: np.ndarray, sfreq: float,
                          window_ms: float = 40.0) -> np.ndarray:
    """
    Sub-QRS moving-average adaptive smoothing.
    window_ms should be well below QRS duration (~80-120 ms).
    """
    win = max(3, int(window_ms / 1000.0 * sfreq))
    if win % 2 == 0:
        win += 1
    return np.convolve(signal, np.ones(win) / win, mode='same')


# ── SIGNAL QUALITY INDEX ──────────────────────────────────────────────────────

def compute_sqi(signal: np.ndarray, sfreq: float) -> dict:
    """
    Multi-metric Signal Quality Index (SQI).

    Returns
    -------
    dict with keys:
      spectral_sqi  : energy ratio of QRS band (5-20 Hz) to total (0-100)
      kurtosis_sqi  : kurtosis-based score — high kurtosis → clear QRS peaks
      baseline_sqi  : penalty for residual low-freq drift
      snr_db        : estimated SNR in dB
      overall_sqi   : weighted composite (0–100)
      quality_label : 'Excellent' | 'Good' | 'Acceptable' | 'Poor'
    """
    from scipy.stats import kurtosis as scipy_kurt

    nperseg = min(256, max(4, len(signal) // 2))
    f, psd = sig.welch(signal, fs=sfreq, nperseg=nperseg)

    _trapz = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
    total_power = float(_trapz(psd, f)) if len(psd) > 1 else 1.0
    if total_power <= 0:
        total_power = 1.0

    # 1. Spectral SQI — QRS energy fraction
    qrs_mask = (f >= 5) & (f <= 20)
    qrs_power = float(_trapz(psd[qrs_mask], f[qrs_mask])) if np.sum(qrs_mask) > 1 else 0.0
    spectral_sqi = float(np.clip(qrs_power / total_power * 100, 0, 100))

    # 2. Kurtosis SQI — sharp QRS peaks increase kurtosis
    kurt = float(scipy_kurt(signal))
    kurtosis_sqi = float(np.clip((kurt / 10.0) * 100, 0, 100))

    # 3. Baseline SQI — penalise large low-freq drift
    try:
        b, a = sig.butter(2, max(0.5 / (0.5 * sfreq), 0.001), btype='low')
        baseline = sig.filtfilt(b, a, signal)
        baseline_ratio = float(np.std(baseline)) / (float(np.std(signal)) + 1e-9)
        baseline_sqi = float(np.clip((1.0 - baseline_ratio) * 100, 0, 100))
    except Exception:
        baseline_sqi = 50.0

    # 4. SNR estimate
    hf_mask = f > 40
    try:
        if np.sum(hf_mask) > 1 and qrs_power > 0:
            noise_power = float(_trapz(psd[hf_mask], f[hf_mask]))
            snr_db = float(np.clip(10 * np.log10(qrs_power / max(noise_power, 1e-12)), -10, 40))
        else:
            snr_db = 20.0
    except Exception:
        snr_db = 20.0

    # 5. Composite SQI
    overall = 0.40 * spectral_sqi + 0.30 * kurtosis_sqi + 0.30 * baseline_sqi
    overall = float(np.clip(overall, 0, 100))

    # 6. Stability Check (R-peak consistency) - placeholder for now
    # In practice, this would be computed after R-peak detection

    label = ("Excellent" if overall >= 75 else
             "Good"      if overall >= 55 else
             "Acceptable" if overall >= 35 else
             "Poor")

    return {
        "spectral_sqi":  round(spectral_sqi, 1),
        "kurtosis_sqi":  round(kurtosis_sqi, 1),
        "baseline_sqi":  round(baseline_sqi, 1),
        "snr_db":        round(snr_db, 1),
        "overall_sqi":   round(overall, 1),
        "quality_label": label,
        "confidence_multiplier": round(np.clip(overall / 100.0, 0.4, 1.0), 2)
    }


# ── ADAPTIVE PREPROCESSING ──────────────────────────────────────────────────

def adaptive_preprocess_ecg(signal: np.ndarray, sfreq: float,
                            sqi: dict,
                            lowcut: float = 0.5, highcut: float = 40.0,
                            filter_order: int = 4) -> tuple[np.ndarray, str]:
    """
    Adaptive Signal Quality-Aware Preprocessing.
    Selects filtering strategy based on SQI score.
    """
    score = sqi.get("overall_sqi", 50)
    
    if score >= 75:
        # HIGH QUALITY: Minimal filtering to preserve QRS morphology
        strategy = "High-Fidelity (Minimal Filtering)"
        clean = preprocess_ecg(signal, sfreq, lowcut=lowcut, highcut=highcut, 
                               remove_baseline=True, noise_method="None", 
                               filter_order=filter_order)
    elif score >= 40:
        # MEDIUM QUALITY: Standard filtering + Powerline suppression
        strategy = "Balanced Adaptive (Standard Denoising)"
        clean = preprocess_ecg(signal, sfreq, lowcut=lowcut, highcut=highcut, 
                               remove_baseline=True, noise_method="Powerline 50Hz", 
                               filter_order=filter_order + 1)
    else:
        # LOW QUALITY: Maximum denoising (Wavelet + Baseline + Notch)
        strategy = "Aggressive Restoration (Max Denoising)"
        clean = preprocess_ecg(signal, sfreq, lowcut=lowcut, highcut=highcut, 
                               remove_baseline=True, noise_method="Wavelet", 
                               filter_order=max(filter_order, 5))
        # Add a secondary notch filter for 60Hz just in case
        clean = apply_notch_filter(clean, sfreq, freq=60.0)
        
    return clean, strategy


# ── FULL PIPELINE ─────────────────────────────────────────────────────────────

def preprocess_ecg(signal: np.ndarray, sfreq: float,
                   lowcut: float = 0.5, highcut: float = 40.0,
                   remove_baseline: bool = True,
                   noise_method: str = 'None',
                   filter_order: int = 4) -> np.ndarray:
    """
    Full ECG preprocessing pipeline.

    Steps (in order):
      1. Baseline wander removal  (optional)
      2. Butterworth bandpass     (order configurable)
      3. Extra noise filter       (Wavelet | Powerline 50/60 Hz | Adaptive)
    """
    clean = np.asarray(signal, dtype=float).copy()

    if remove_baseline:
        clean = remove_baseline_wander(clean, sfreq)

    clean = apply_bandpass_filter(clean, sfreq, lowcut, highcut, order=filter_order)

    if noise_method == "Wavelet":
        clean = apply_wavelet_denoise(clean)
    elif noise_method == "Powerline 50Hz":
        clean = apply_notch_filter(clean, sfreq, freq=50.0)
        if sfreq > 210:
            clean = apply_notch_filter(clean, sfreq, freq=100.0)
    elif noise_method == "Powerline 60Hz":
        clean = apply_notch_filter(clean, sfreq, freq=60.0)
        if sfreq > 250:
            clean = apply_notch_filter(clean, sfreq, freq=120.0)
    elif noise_method == "Adaptive":
        clean = apply_adaptive_filter(clean, sfreq)

    return clean
