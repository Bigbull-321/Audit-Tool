import streamlit as st
import pandas as pd
import numpy as np
from math import log10, sqrt
from io import BytesIO

# ---------------------------------
# Page Configuration
# ---------------------------------
st.set_page_config(
    page_title="Z-Score + Benford's Law",
    page_icon="",
    layout="wide"
)

st.title("Z-Score + Benford's Law")

# ---------------------------------
# Upload File (Common)
# ---------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx", "xls"]
)

if uploaded_file is not None:

    try:
        df = pd.read_excel(uploaded_file)

        st.success(f"✅ File Loaded Successfully ({len(df)} Records)")

        # ---------------------------------
        # Tabs
        # ---------------------------------
        tab1, tab2 = st.tabs(["Benford's Law", "Z-Score"])

        # ==========================================================
        # TAB 1 : BENFORD'S LAW
        # ==========================================================
        with tab1:

            st.header("Benford's Law Analysis")

            selected_column = st.selectbox(
                "Select Column",
                df.columns,
                key="benford_column"
            )

            if st.button("Run Benford Analysis", key="benford_button"):

                def first_digit(value):
                    try:
                        if pd.isna(value):
                            return np.nan

                        text = str(value).replace(",", "").strip()
                        num = float(text)

                        if num <= 0:
                            return np.nan

                        for ch in text:
                            if ch.isdigit() and ch != "0":
                                return int(ch)

                        return np.nan

                    except:
                        return np.nan

                analysis_df = df.copy()

                analysis_df["First_Digit"] = analysis_df[selected_column].apply(first_digit)

                df_valid = analysis_df[
                    analysis_df["First_Digit"].between(1, 9)
                ].copy()

                n = len(df_valid)

                if n == 0:
                    st.error("No valid numeric values found.")
                else:

                    results = []

                    for digit in range(1, 10):

                        actual_count = (df_valid["First_Digit"] == digit).sum()

                        actual_freq = (actual_count / n) * 100

                        benford_prob = log10(1 + (1 / digit))

                        benford_freq = benford_prob * 100

                        expected_count = n * benford_prob

                        std_error = sqrt(
                            n * benford_prob * (1 - benford_prob)
                        )

                        z_score = (
                            (actual_count - expected_count) / std_error
                            if std_error > 0 else np.nan
                        )

                        results.append([
                            digit,
                            round(actual_freq, 2),
                            round(benford_freq, 2),
                            int(actual_count),
                            round(z_score, 4)
                        ])

                    summary_df = pd.DataFrame(
                        results,
                        columns=[
                            "Digit",
                            "Actual Frequency (%)",
                            "Benford Frequency (%)",
                            "Actual Count",
                            "Z-Score"
                        ]
                    )

                    st.success("Benford Analysis Completed")

                    st.dataframe(
                        summary_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.info(f"Records Analyzed : {n}")

                    output = BytesIO()

                    with pd.ExcelWriter(output, engine="openpyxl") as writer:

                        summary_df.to_excel(
                            writer,
                            sheet_name="Benford Summary",
                            index=False
                        )

                        for digit in range(1, 10):

                            digit_df = df_valid[
                                df_valid["First_Digit"] == digit
                            ]

                            digit_df.to_excel(
                                writer,
                                sheet_name=f"Digit_{digit}",
                                index=False
                            )

                    output.seek(0)

                    st.download_button(
                        "📥 Download Benford Report",
                        data=output,
                        file_name="Benford_Analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        # ==========================================================
        # TAB 2 : Z SCORE
        # ==========================================================
        with tab2:

            st.header("Z-Score Anomaly Detection")

            selected_column = st.selectbox(
                "Select Column",
                df.columns,
                key="zscore_column"
            )

            threshold = st.number_input(
                "Z-Score Threshold",
                min_value=0.1,
                value=1.96,
                step=0.01,
                key="threshold"
            )

            if st.button("Run Z-Score", key="zscore_button"):

                result_df = df.copy()

                result_df[selected_column] = (
                    result_df[selected_column]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )

                result_df[selected_column] = pd.to_numeric(
                    result_df[selected_column],
                    errors="coerce"
                )

                if result_df[selected_column].dropna().empty:
                    st.error("Selected column does not contain numeric values.")
                else:

                    result_df = result_df.dropna(subset=[selected_column])

                    std_val = result_df[selected_column].std()

                    if std_val == 0:
                        st.error("Standard deviation is zero.")
                    else:

                        mean_val = result_df[selected_column].mean()

                        result_df["Z_Score"] = (
                            (result_df[selected_column] - mean_val) / std_val
                        )

                        result_df["Status"] = np.where(
                            result_df["Z_Score"].abs() > threshold,
                            "Anomaly",
                            "Normal"
                        )

                        anomaly_df = result_df[
                            result_df["Status"] == "Anomaly"
                        ]

                        st.success(
                            f"{len(anomaly_df)} anomaly record(s) found."
                        )

                        if anomaly_df.empty:
                            st.info("No anomalies found.")
                        else:

                            st.dataframe(
                                anomaly_df,
                                use_container_width=True
                            )

                            output = BytesIO()

                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                anomaly_df.to_excel(
                                    writer,
                                    sheet_name="Anomalies",
                                    index=False
                                )

                            output.seek(0)

                            st.download_button(
                                "📥 Download Anomaly Excel",
                                data=output,
                                file_name="ZScore_Anomalies.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )

    except Exception as e:
        st.error(f"Error: {e}")