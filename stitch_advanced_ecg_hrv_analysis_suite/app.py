import streamlit as st

st.set_page_config(
    page_title="Advanced ECG & HRV Analysis Suite",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🫀 Comprehensive ECG & HRV Analysis System")
    st.markdown("---")
    
    st.markdown("""
    ### Welcome to the Advanced Biomedical Signal Processing Suite
    This multi-dashboard tool provides a fully functional, end-to-end algorithmic pipeline for analyzing Electrocardiogram (ECG) data and extracting robust Heart Rate Variability (HRV) metrics.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔄 Algorithmic Pipeline")
        # Mermaid code for pipeline
        mermaid_code = """
        graph TD
            A(1. ECG Acquisition) --> B(2. Preprocessing)
            B --> C(3. R-Peak Detection)
            C --> D(4. RR Interval Extraction)
            D --> E{5. Ectopic Correction}
            E -- Yes --> F(Interpolation)
            E -- No --> G(6. Analysis)
            F --> G
            G --> H[Time Domain]
            G --> I[Freq Domain]
            G --> J[Non-Linear]
            H --> K(Multi-Dashboard Presentation)
            I --> K
            J --> K
        """
        # st.markdown doesn't native render mermaid without plugin, we can use an image or simply text for now
        st.info("Pipeline Flow: ECG → Preprocessing → R-Peaks → RR → Ectopic Removal → HRV Analysis → Dashboards")
        
        st.markdown("""
        **How to navigate the suite:**
        1. **Dashboard 1 (Input):** Upload your ECG file (`.csv`, `.edf`, etc.).
        2. **Dashboard 2 (Preprocessing):** Filter noise and remove baseline wander.
        3. **Dashboard 3 (R-Peak):** Extract fiducial points.
        4. **Dashboards 4 & 5 (RR & Ectopic):** Manage arrhythmias or artifacts.
        5. **Dashboards 6-8 (HRV Metrics):** Explore complex metrics in different domains.
        6. **Dashboard 10 (Comparison):** Load multiple files for cross-patient/cohort analysis.
        """)
        
    with col2:
        st.subheader("💡 Key Features")
        st.success("✅ Multi-file support")
        st.success("✅ Real-time pipeline configuration")
        st.success("✅ Robust R-peak extraction")
        st.success("✅ Advanced Interpolation logic")
        st.success("✅ Time, Frequency, & Non-linear HRV")

if __name__ == "__main__":
    main()
