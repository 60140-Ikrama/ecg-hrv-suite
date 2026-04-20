"""
Signal Processing: Bandpass filtering, baseline wander removal, and noise filtering.
"""
import numpy as np
import scipy.signal as sig


def apply_bandpass_filter(signal: np.ndarray, sfreq: float, lowcut: float = 0.5, highcut: float = 40.0, order: int = 3):
    nyquist = 0.5 * sfreq
    low = lowcut / nyquist
    high = highcut / nyquist
    high = min(high, 0.99)
    low = max(low, 0.001)
    if low >= high:
        high = min(low + 0.01, 0.99)
    b, a = sig.butter(order, [low, high], btype='band')
    return sig.filtfilt(b, a, signal)


def remove_baseline_wander(signal: np.ndarray, sfreq: float, cutoff: float = 0.5):
    nyquist = 0.5 * sfreq
    c = cutoff / nyquist
    c = max(min(c, 0.99), 0.001)
    b, a = sig.butter(3, c, btype='high')
    return sig.filtfilt(b, a, signal)


def apply_notch_filter(signal: np.ndarray, sfreq: float, freq: float = 50.0, Q: float = 30.0):
    """Notch filter for powerline interference."""
    b, a = sig.iirnotch(freq / (0.5 * sfreq), Q)
    return sig.filtfilt(b, a, signal)


def apply_wavelet_denoise(signal: np.ndarray):
    """Wavelet-based denoising."""
    try:
        import pywt
        coeffs = pywt.wavedec(signal, 'db4', level=4)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        uthresh = sigma * np.sqrt(2 * np.log(max(len(signal), 1)))
        coeffs[1:] = [pywt.threshold(c, value=uthresh, mode='soft') for c in coeffs[1:]]
        denoised = pywt.waverec(coeffs, 'db4')
        return denoised[:len(signal)]
    except ImportError:
        return signal


def preprocess_ecg(signal: np.ndarray, sfreq: float,
                   lowcut: float = 0.5, highcut: float = 40.0,
                   remove_baseline: bool = True,
                   noise_method: str = 'None') -> np.ndarray:
    """Full preprocessing pipeline."""
    clean = signal.copy().astype(float)
    if remove_baseline:
        clean = remove_baseline_wander(clean, sfreq)
    clean = apply_bandpass_filter(clean, sfreq, lowcut, highcut)
    if noise_method == "Wavelet":
        clean = apply_wavelet_denoise(clean)
    elif noise_method == "Powerline 50Hz":
        clean = apply_notch_filter(clean, sfreq, freq=50.0)
    elif noise_method == "Powerline 60Hz":
        clean = apply_notch_filter(clean, sfreq, freq=60.0)
    return clean
