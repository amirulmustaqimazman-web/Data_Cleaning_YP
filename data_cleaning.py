import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(
    page_title="Data Cleaning App",
    layout="wide",
    page_icon="🧼",
    initial_sidebar_state="expanded"
)

st.title("🧼 Data Cleaning App")
st.write("Upload your dataset, clean missing values and duplicates, then download the cleaned file.")

# Helper: load file
def load_file(file):
    if file is None:
        return None
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type. Please upload CSV or Excel.")
        return None

# File Upload
st.sidebar.header("Upload Your File")
uploaded_file = st.sidebar.file_uploader(
    "Drag & drop or browse a CSV / Excel file",
    type=["csv", "xlsx", "xls"]
)

# We will store the cleaned DataFrame in session_state
if "df_clean" not in st.session_state:
    st.session_state.df_clean = None

if uploaded_file is not None:
    df_original = load_file(uploaded_file)
    if df_original is not None:
        # Initialise clean df if first time
        if st.session_state.df_clean is None:
            st.session_state.df_clean = df_original.copy()

df = st.session_state.df_clean

if df is not None:
    st.success(f"File uploaded successfully! Current clean data shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Preview
    st.subheader("🔍 Data Preview")
    st.dataframe(df.head(20))

    # Missing Values & Duplicates Checker
    st.subheader("📉 Missing Values and Duplicates Checker")

    missing_df = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(2)
    })
    st.markdown("**Missing values per column**")
    st.dataframe(missing_df)

    dup_count = df.duplicated().sum()
    st.markdown(f"**Number of duplicate rows:** `{dup_count}`")

    # Use columns layout for buttons
    st.markdown("### 🧹 Cleaning Actions")

    col1, col2, col3, col4 = st.columns(4)

    # 1) Drop rows with ANY missing values
    with col1:
        if st.button("Drop rows with missing"):
            before = df.shape[0]
            df = df.dropna()
            after = df.shape[0]
            st.session_state.df_clean = df
            st.success(f"Dropped {before - after} rows containing missing values.")

    # 2) Handle missing values (impute)
    with col2:
        if st.button("Handle missing (auto)"):
            # Numeric: fill with median
            num_cols = df.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)

            # Categorical: fill with mode
            cat_cols = [c for c in df.columns if c not in num_cols]
            for col in cat_cols:
                if df[col].isna().any():
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col].fillna(mode_val.iloc[0], inplace=True)

            st.session_state.df_clean = df
            st.success("Missing values handled: numeric → median, categorical → mode.")

    # 3) Drop duplicate rows
    with col3:
        if st.button("Drop duplicate rows"):
            before = df.shape[0]
            df = df.drop_duplicates()
            after = df.shape[0]
            st.session_state.df_clean = df
            st.success(f"Dropped {before - after} duplicate rows.")

    # 4) Reset to original uploaded data
    with col4:
        if st.button("Reset to original"):
            if uploaded_file is not None:
                st.session_state.df_clean = load_file(uploaded_file)
                df = st.session_state.df_clean
                st.info("Clean data has been reset to the original uploaded file.")
            else:
                st.warning("No file uploaded to reset from.")

    # Show updated info after actions
    st.markdown("### 📊 Cleaned Data Preview")
    st.dataframe(df.head(20))

    st.markdown("### ℹ️ Cleaned Data Info")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

    # Download Cleaned File
    st.subheader("💾 Download Cleaned File")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download cleaned data as CSV",
        data=csv_bytes,
        file_name="cleaned_data.csv",
        mime="text/csv"
    )

else:
    st.info("Upload a CSV or Excel file from the sidebar to start cleaning.")