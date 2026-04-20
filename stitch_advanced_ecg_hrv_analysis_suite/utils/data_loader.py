import pandas as pd
import numpy as np
import scipy.io as sio

def load_ecg_file(uploaded_file):
    """
    Load ECG from an uploaded file object.
    Supports CSV, TXT, MAT.
    Returns:
        np.array: 1D array of the ECG signal.
    """
    if uploaded_file is None:
        return None
    
    file_name = uploaded_file.name.lower()
    
    try:
        if file_name.endswith('.csv'):
            # Assume single column or look for 'ecg' column
            df = pd.read_csv(uploaded_file)
            # Find the best column
            ecg_col = next((col for col in df.columns if 'ecg' in col.lower()), df.columns[0])
            sig = df[ecg_col].values
            
        elif file_name.endswith('.txt'):
            sig = np.loadtxt(uploaded_file)
            
        elif file_name.endswith('.mat'):
            mat = sio.loadmat(uploaded_file)
            # Extract first 1D array or variable containing 'ecg'
            sig = None
            for key in mat:
                if not key.startswith('__'):
                    if 'ecg' in key.lower():
                        sig = np.squeeze(mat[key])
                        break
            if sig is None:
                # fallback to first valid numeric array
                for key in mat:
                    if not key.startswith('__'):
                        val = np.squeeze(mat[key])
                        if val.ndim == 1:
                            sig = val
                            break
            
        elif file_name.endswith('.edf'):
            try:
                import mne
                # Streamlit uploaded files are often byte buffers. MNE wants a path.
                # Since Streamlit UploadedFile is in memory, we need to save it temporarily
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.edf') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                raw = mne.io.read_raw_edf(tmp_path, preload=True, verbose=False)
                # Take first channel
                sig = raw.get_data()[0, :]
                os.remove(tmp_path)
            except ImportError:
                raise ImportError("mne library is required to read .edf files")
                
        else:
            raise ValueError(f"Unsupported file format: {file_name}")
        
        # Ensure 1D and numeric
        sig = np.asarray(sig, dtype=float).flatten()
        
        # Remove nans
        sig = sig[~np.isnan(sig)]
        return sig
        
    except Exception as e:
        raise Exception(f"Error loading {file_name}: {e}")
