import scipy.signal as sig
import pywt
import numpy as np

def apply_bandpass_filter(signal: np.ndarray, sfreq: float, lowcut: float = 0.5, highcut: float = 40.0, order: int = 3):
    """
    Applies a Butterworth bandpass filter.
    """
    nyquist = 0.5 * sfreq
    low = lowcut / nyquist
    high = highcut / nyquist
    
    # Handle edge case where highcut >= nyquist
    if high >= 1.0:
        high = 0.99
    
    b, a = sig.butter(order, [low, high], btype='band')
    return sig.filtfilt(b, a, signal)

def remove_baseline_wander(signal: np.ndarray, sfreq: float):
    """
    Removes baseline wander using a high-pass filter (0.5 Hz is standard for ECG)
    or median filtering. Here we use an IIR Butterworth high-pass.
    """
    nyquist = 0.5 * sfreq
    cutoff = 0.5 / nyquist
    b, a = sig.butter(3, cutoff, btype='high')
    return sig.filtfilt(b, a, signal)

def apply_noise_filter(signal: np.ndarray, method: str = 'None'):
    """
    Apply additional noise filtering (e.g. Wavelet denoising).
    """
    if method == "None":
        return signal
    elif method == "Wavelet":
        # Wavelet thresholding
        coeffs = pywt.wavedec(signal, 'db4', level=4)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        uthresh = sigma * np.sqrt(2 * np.log(len(signal)))
        coeffs[1:] = (pywt.threshold(i, value=uthresh, mode='soft') for i in coeffs[1:])
        return pywt.waverec(coeffs, 'db4')
    elif method == "Powerline Removal (50/60 Hz)":
        # This typically needs sfreq. We will just return the signal here 
        # and recommend explicit notch filtering if needed.
        return signal
    return signal

def preprocess_ecg(signal: np.ndarray, sfreq: float, 
                   lowcut: float = 0.5, highcut: float = 40.0, 
                   remove_baseline: bool = True, noise_method: str = 'None'):
    """
    Full preprocessing pipeline.
    """
    clean_sig = signal.copy()
    if remove_baseline:
        clean_sig = remove_baseline_wander(clean_sig, sfreq)
        
    clean_sig = apply_bandpass_filter(clean_sig, sfreq, lowcut, highcut)
    clean_sig = apply_noise_filter(clean_sig, method=noise_method)
    
    return clean_sig
