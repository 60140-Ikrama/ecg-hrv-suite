import numpy as np
import scipy.signal as sig
from scipy.interpolate import interp1d

def remove_ectopic_beats(rr_ms: np.ndarray, method="linear", threshold=0.2):
    """
    Detects and corrects ectopic beats (outliers in RR interval sequence).
    threshold: deviation factor from median RR (e.g., 0.2 means 20% deviation).
    method: "linear" or "spline" for interpolation.
    
    Returns:
        clean_rr: the interpolated RR sequence
        outliers: boolean array indicating which RR intervals were identified as ectopic
    """
    if len(rr_ms) < 5:
        return rr_ms, np.zeros(len(rr_ms), dtype=bool)

    # Use a rolling median to detect local outliers
    # Window size 5
    import pandas as pd
    series = pd.Series(rr_ms)
    rolling_median = series.rolling(window=5, center=True).median()
    # Filling NaNs at the edges with global median or nearest valid
    rolling_median = rolling_median.fillna(series.median())
    
    # Calculate relative deviation
    deviation = np.abs(series - rolling_median) / rolling_median
    
    outliers = (deviation > threshold).values
    
    clean_rr = rr_ms.copy()
    if np.any(outliers):
        valid_indices = np.where(~outliers)[0]
        outlier_indices = np.where(outliers)[0]
        
        if len(valid_indices) > 1:
            try:
                if method.lower() == "spline":
                    # degree 3 if enough valid points
                    k = 3 if len(valid_indices) > 3 else 1
                    interp_func = interp1d(valid_indices, clean_rr[valid_indices], kind=k, fill_value="extrapolate")
                else:
                    # linear default
                    interp_func = interp1d(valid_indices, clean_rr[valid_indices], kind='linear', fill_value="extrapolate")
                
                clean_rr[outlier_indices] = interp_func(outlier_indices)
            except Exception as e:
                # Fallback to linear if spline fails
                interp_func = interp1d(valid_indices, clean_rr[valid_indices], kind='linear', fill_value="extrapolate")
                clean_rr[outlier_indices] = interp_func(outlier_indices)
                
    return clean_rr, outliers

def get_time_domain_hrv(rr_ms: np.ndarray):
    """
    Calculates time-domain HRV metrics.
    """
    if len(rr_ms) < 2:
        return {}
    
    mean_rr = np.mean(rr_ms)
    sdnn = np.std(rr_ms, ddof=1)
    
    diff_rr = np.diff(rr_ms)
    rmssd = np.sqrt(np.mean(diff_rr**2))
    
    nn50 = np.sum(np.abs(diff_rr) > 50)
    pnn50 = (nn50 / len(diff_rr)) * 100 if len(diff_rr) > 0 else 0
    
    return {
        "Mean RR (ms)": mean_rr,
        "SDNN (ms)": sdnn,
        "RMSSD (ms)": rmssd,
        "NN50": nn50,
        "pNN50 (%)": pnn50
    }

def get_freq_domain_hrv(rr_ms: np.ndarray, vlf_band=(0.0, 0.04), lf_band=(0.04, 0.15), hf_band=(0.15, 0.4)):
    """
    Calculates Frequency-domain HRV using Welch's method via resampling RR sequence to a continuous time series.
    """
    if len(rr_ms) < 10:
        return None, None, None
    
    # 1. Resample RR intervals (which are unevenly spaced) at 4 Hz
    fs_resample = 4.0 
    t = np.cumsum(rr_ms) / 1000.0 # Time axis in seconds
    t = t - t[0] # start from 0
    
    t_interp = np.arange(0, t[-1], 1.0 / fs_resample)
    f_interp = interp1d(t, rr_ms, kind='cubic', fill_value="extrapolate")
    rr_interp = f_interp(t_interp)
    
    # 2. Compute PSD using Welch's method
    # Nperseg should be around 256 for sufficient resolution at 4Hz, 
    # but bounded by length of resampled data
    nperseg = min(256, len(rr_interp))
    freqs, psd = sig.welch(rr_interp, fs=fs_resample, nperseg=nperseg, scaling='density')
    
    # 3. Calculate Power in bands
    def band_power(f_min, f_max):
        idx = np.logical_and(freqs >= f_min, freqs < f_max)
        # Using trapezoidal integration
        if np.sum(idx) > 1:
            # Fallback to scipy or new numpy 2.0 syntax
            try:
                return np.trapezoid(psd[idx], freqs[idx])
            except AttributeError:
                # Fallback for old numpy versions just in case
                return np.trapz(psd[idx], freqs[idx])
        return 0.0

    vlf = band_power(*vlf_band)
    lf = band_power(*lf_band)
    hf = band_power(*hf_band)
    
    ratio = lf / hf if hf > 0 else float('nan')
    total_power = vlf + lf + hf
    
    metrics = {
        "VLF Power": vlf,
        "LF Power": lf,
        "HF Power": hf,
        "LF/HF Ratio": ratio,
        "Total Power": total_power
    }
    
    return metrics, freqs, psd

def get_nonlinear_hrv(rr_ms: np.ndarray):
    """
    Computes Poincare (SD1, SD2) metrics.
    """
    if len(rr_ms) < 2:
        return {}
    
    rr_n = rr_ms[:-1]
    rr_n1 = rr_ms[1:]
    
    sd1 = np.std(np.subtract(rr_n, rr_n1) / np.sqrt(2), ddof=1)
    sd2 = np.std(np.add(rr_n, rr_n1) / np.sqrt(2), ddof=1)
    
    return {
        "SD1 (ms)": sd1,
        "SD2 (ms)": sd2,
        "SD1/SD2": sd1/sd2 if sd2 > 0 else float('nan')
    }
