import streamlit as st
import pandas as pd
import numpy as np
import io

# Page configuration
st.set_page_config(
    page_title="Data Cleaning App",
    layout="wide",
    page_icon="🧼",
    initial_sidebar_state="expanded"
)

st.title("🧼 Data Cleaning App")
st.write("Upload your dataset, clean missing values and duplicates, then download the cleaned file.")

# Configuration for Missing Values
MISSING_VALUES_LIST = [
    "", " ", "NA", "N/A", "na", "NaN", "None", "NONE",
    "UNKNOWN", "Unknown", "error", "ERROR", "nan"
]

# Helper: safely load a CSV file
def load_file(file):
    """Load the uploaded file as a CSV, converting known placeholders to NaN."""
    if file is None:
        return None

    filename = file.name.lower()

    # Check extension: only allow .csv
    if not filename.endswith(".csv"):
        st.error("The uploaded file is not in CSV format. Please upload a CSV file.")
        return None
    
    # Reload the file pointer to ensure proper reading after checking (safety measure)
    file.seek(0) 

    try:
        df = pd.read_csv(
            file,
            # Use the global list to ensure all known placeholders are NaN from the start
            na_values=MISSING_VALUES_LIST, 
            keep_default_na=True
        )

        # Handle empty CSV file (no columns / no data)
        if df.empty:
            st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
            return None

        return df

    except Exception as e:
        st.error(f"Error while reading the CSV file: {e}")
        return None

# File uploader (CSV only)
uploaded_file = st.sidebar.file_uploader(
    "Upload your CSV file",
    type=["csv"]
)

# Session state: store original and cleaned dataframe
if "df_original" not in st.session_state:
    st.session_state.df_original = None
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None

# Load file and initialize clean dataframe
if uploaded_file is not None:
    # Load original data safely using the helper
    df_original = load_file(uploaded_file)
    
    if df_original is not None:
        # Initialize original and clean dataframes in state
        st.session_state.df_original = df_original
        # Only overwrite df_clean if it's the first load or after a reset
        if st.session_state.df_clean is None or st.session_state.df_clean.empty:
             st.session_state.df_clean = df_original.copy()

        st.success(
            f"CSV file uploaded successfully! "
            f"Shape: {df_original.shape[0]} rows × {df_original.shape[1]} columns"
        )


# Work with the cleaned dataframe from session_state
df = st.session_state.df_clean

# Main cleaning UI
if df is not None:
    
    st.info(f"Current clean data shape: **{df.shape[0]}** rows × **{df.shape[1]}** columns")

    # Data preview
    st.subheader("🔍 Data Preview")
    st.dataframe(df.head(10)) # Adjusted to show fewer rows for compactness

    # Missing & Duplicates Checker
    st.subheader("📉 Missing Values and Duplicates Checker")

    # Only count True NaN/NaT values
    missing_df = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(2)
    }).sort_values(by="missing_count", ascending=False)
    
    st.markdown("**Missing values per column**")
    # Filter to only show columns with missing data
    st.dataframe(missing_df[missing_df["missing_count"] > 0]) 

    dup_count = df.duplicated().sum()
    st.markdown(f"**Number of duplicate rows:** `{dup_count}`")

    # Cleaning actions
    st.markdown("### 🧹 Cleaning Actions")

    col1, col2, col3, col4 = st.columns(4)

    # 1) Handle missing values (auto-impute)
    with col1:
        if st.button("Handle missing (Impute)", key="impute_auto"):
            
            # Work on a fresh copy
            df_temp = df.copy()
            
            # 1. Numeric columns: fill missing with median
            num_cols = df_temp.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                # Use mean only on non-NA values
                impute_value = df_temp[col].median()
                df_temp[col].fillna(impute_value, inplace=True)

            # 2. Categorical columns: fill missing with "NaN" placeholder
            cat_cols = df_temp.select_dtypes(include=['object']).columns
            for col in cat_cols:
                # Fill true NaN with a categorical marker
                df_temp[col].fillna('NaN', inplace=True)
            
            # Save updates back to session state
            st.session_state.df_clean = df_temp

            st.success("Numeric missing values filled with **median**. Categorical missing values filled with **'NaN'**.")

    # 2) Drop rows with ANY missing values
    with col2:
        if st.button("Drop rows with missing", key="drop_na"):
            before = df.shape[0]
            df = df.dropna()
            after = df.shape[0]
            st.session_state.df_clean = df
            st.success(f"Dropped **{before - after}** rows containing missing values.")

    
    # 3) Drop duplicate rows
    with col3:
        if st.button("Drop duplicate rows", key="drop_dupes"):
            before = df.shape[0]
            df = df.drop_duplicates()
            after = df.shape[0]
            st.session_state.df_clean = df
            st.success(f"Dropped **{before - after}** duplicate rows.")

    # 4) Reset to original
    with col4:
        if st.button("Reset to original", key="reset_data"):
            if st.session_state.df_original is not None:
                # Reset df_clean to the stored original copy
                st.session_state.df_clean = st.session_state.df_original.copy()
                df = st.session_state.df_clean
                st.info("Clean data has been **reset** to the original uploaded CSV file.")
            else:
                st.warning("No file uploaded to reset from.")

    # Updated Preview & Info
    st.markdown("### 📊 Cleaned Data Preview")
    st.dataframe(df.head(10))

    st.markdown("### ℹ️ Cleaned Data Info")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

    # Download cleaned file
    st.subheader("💾 Download Cleaned File")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download cleaned data as CSV",
        data=csv_bytes,
        file_name="cleaned_data.csv",
        mime="text/csv"
    )
