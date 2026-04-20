"""
Data Loader: Supports CSV, TXT, MAT, EDF, and DAT files.
"""
import pandas as pd
import numpy as np
import scipy.io as sio
import io


def load_ecg_file(uploaded_file):
    """
    Load ECG signal from an uploaded Streamlit file object.
    Supports: .csv, .txt, .mat, .edf, .dat
    Returns: (signal: np.ndarray, detected_fs: float or None, info: dict)
    """
    if uploaded_file is None:
        return None, None, {}

    file_name = uploaded_file.name.lower()
    info = {"filename": uploaded_file.name}

    try:
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            # Smart column detection
            ecg_col = None
            for col in df.columns:
                if any(k in col.lower() for k in ['ecg', 'ekg', 'signal', 'mV', 'mv', 'ch1', 'ii']):
                    ecg_col = col
                    break
            if ecg_col is None:
                # try the likely numeric columns, pick the one with most variability
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_cols:
                    raise ValueError("No numeric columns found in CSV.")
                ecg_col = max(numeric_cols, key=lambda c: df[c].std())
            sig = df[ecg_col].values.astype(float)
            info["column"] = ecg_col
            info["total_columns"] = len(df.columns)

        elif file_name.endswith('.txt'):
            raw = uploaded_file.read()
            try:
                sig = np.loadtxt(io.BytesIO(raw))
            except Exception:
                # Try space/comma-separated
                df = pd.read_csv(io.BytesIO(raw), sep=r'\s+|,', engine='python', header=None)
                # Use highest-variance numeric column
                numeric = df.select_dtypes(include=[np.number])
                sig = numeric.iloc[:, numeric.std().idxmax()].values.astype(float)

        elif file_name.endswith('.dat'):
            raw_bytes = uploaded_file.read()
            # Try WFDB-style ASCII first
            try:
                sig = np.loadtxt(io.BytesIO(raw_bytes))
            except Exception:
                # Try binary int16 (PhysioBank format stores as int16)
                try:
                    sig = np.frombuffer(raw_bytes, dtype=np.int16).astype(float)
                except Exception:
                    sig = np.frombuffer(raw_bytes, dtype=np.float32).astype(float)
            # If 2D, pick first column
            if sig.ndim == 2:
                sig = sig[:, 0]

        elif file_name.endswith('.mat'):
            mat = sio.loadmat(uploaded_file)
            sig = None
            # Try to find ECG-named variable first
            for key in mat:
                if not key.startswith('__'):
                    if any(k in key.lower() for k in ['ecg', 'ekg', 'signal', 'val']):
                        candidate = np.squeeze(mat[key]).astype(float)
                        if candidate.ndim == 1 and len(candidate) > 10:
                            sig = candidate
                            info["mat_key"] = key
                            break
            if sig is None:
                # Fallback: use first 1D array
                for key in mat:
                    if not key.startswith('__'):
                        candidate = np.squeeze(mat[key])
                        if candidate.ndim == 1 and len(candidate) > 10:
                            sig = candidate.astype(float)
                            info["mat_key"] = key
                            break
            if sig is None:
                raise ValueError("No valid 1D ECG array found in .mat file.")

        elif file_name.endswith('.edf'):
            try:
                import mne
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.edf') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                raw = mne.io.read_raw_edf(tmp_path, preload=True, verbose=False)
                # Find ECG channel
                ecg_ch = None
                for ch in raw.ch_names:
                    if any(k in ch.lower() for k in ['ecg', 'ekg', 'ii']):
                        ecg_ch = ch
                        break
                if ecg_ch:
                    sig = raw.get_data(picks=[ecg_ch])[0, :]
                    info["channel"] = ecg_ch
                else:
                    sig = raw.get_data()[0, :]
                    info["channel"] = raw.ch_names[0]
                detected_fs = raw.info['sfreq']
                os.remove(tmp_path)
                sig = np.asarray(sig, dtype=float).flatten()
                sig = sig[~np.isnan(sig)]
                return sig, detected_fs, info
            except ImportError:
                raise ImportError("The 'mne' package is required to read .edf files. Run: pip install mne")

        else:
            raise ValueError(f"Unsupported file format. Got: '{file_name}'")

        # Final cleanup
        sig = np.asarray(sig, dtype=float).flatten()
        sig = sig[~np.isnan(sig)]
        sig = sig[~np.isinf(sig)]

        if len(sig) == 0:
            raise ValueError("Signal is empty after loading.")

        return sig, None, info

    except Exception as e:
        raise Exception(f"Error loading '{uploaded_file.name}': {e}")
