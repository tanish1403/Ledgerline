"""Interactive Reliability Analytics View."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from reliability.stats import kaplan_meier, outliers, weibull_fit


def render_analytics_view() -> None:
    st.header("📊 Interactive Reliability Analytics")
    st.caption("Perform Weibull fitting, Kaplan-Meier survival curves, and outlier detection.")

    data_source = st.radio(
        "Choose Data Source:",
        ["NASA C-MAPSS Turbofan (Sample)", "Custom Manual Input"],
        horizontal=True,
    )

    durations: list[float] = []
    events: list[int] = []

    if data_source == "NASA C-MAPSS Turbofan (Sample)":
        sample_durations = [
            112.0,
            145.0,
            166.0,
            180.0,
            192.0,
            205.0,
            218.0,
            225.0,
            238.0,
            245.0,
            256.0,
            269.0,
            281.0,
            299.0,
            310.0,
            325.0,
            341.0,
            355.0,
            362.0,
            378.0,
        ]
        durations = sample_durations
        events = [1] * len(sample_durations)
        df_preview = pd.DataFrame({"Unit": range(1, len(durations) + 1), "Cycles": durations})
        st.dataframe(df_preview.T, use_container_width=True)

    elif data_source == "Custom Manual Input":
        raw_durations = st.text_input(
            "Enter durations (comma-separated):",
            "100.5, 120.3, 145.0, 150.2, 175.4, 210.0, 230.1, 245.5",
        )
        try:
            durations = [float(x.strip()) for x in raw_durations.split(",") if x.strip()]
            events = [1] * len(durations)
        except ValueError:
            st.error("Invalid numbers entered.")
            return

    if not durations:
        st.warning("No data available.")
        return

    tab1, tab2, tab3 = st.tabs(
        ["Weibull Distribution", "Kaplan-Meier Survival", "Outlier Detection"]
    )

    with tab1:
        st.subheader("Weibull Parameter Estimation")
        try:
            w_res: dict[str, Any] = weibull_fit(durations, events)
            shape = w_res["shape"]
            scale = w_res["scale"]
            aic = w_res["AIC"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Shape Parameter (β)", f"{shape:.3f}")
            col2.metric("Scale Parameter (η)", f"{scale:.2f} cycles")
            col3.metric("Model AIC", f"{aic:.2f}")

            if shape < 1.0:
                st.warning("⚠️ **Infant Mortality (β < 1)**: Decreasing failure rate.")
            elif 0.95 <= shape <= 1.05:
                st.info("ℹ️ **Random Failures (β ≈ 1)**: Constant failure rate.")
            else:
                st.success("✅ **Wear-Out Phase (β > 1)**: Increasing failure rate.")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
            t_max = max(durations) * 1.3
            t = np.linspace(0.1, t_max, 200)

            pdf = (shape / scale) * ((t / scale) ** (shape - 1)) * np.exp(-((t / scale) ** shape))
            cdf = 1.0 - np.exp(-((t / scale) ** shape))

            ax1.plot(t, pdf, color="#0284c7", lw=2, label="PDF")
            ax1.hist(durations, bins=8, density=True, alpha=0.3, color="#0284c7", edgecolor="black")
            ax1.set_title("PDF f(t)")
            ax1.grid(True, linestyle="--", alpha=0.5)

            ax2.plot(t, cdf, color="#e11d48", lw=2, label="CDF")
            ax2.axhline(0.632, color="gray", linestyle=":", label="63.2% Life")
            ax2.set_title("CDF F(t)")
            ax2.grid(True, linestyle="--", alpha=0.5)

            plt.tight_layout()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error computing Weibull fit: {e}")

    with tab2:
        st.subheader("Kaplan-Meier Survival Function")
        try:
            km_res = kaplan_meier(durations, events)
            timeline = km_res["timeline"]
            sf = km_res["survival_function"]
            median_life = km_res["median_survival_time"]

            st.metric("Estimated Median Survival Life", f"{median_life:.2f} cycles")

            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.step(timeline, sf, where="post", color="#16a34a", lw=2, label="Survival S(t)")
            ax.axhline(0.5, color="gray", linestyle="--", alpha=0.7, label="50% Survival")
            ax.set_title("Kaplan-Meier Survival Function S(t)")
            ax.set_xlabel("Operational Cycles")
            ax.set_ylabel("Survival Probability")
            ax.set_ylim(-0.05, 1.05)
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.legend()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error computing Kaplan-Meier: {e}")

    with tab3:
        st.subheader("Statistical Outlier Detection")
        method = st.selectbox("Detection Method:", ["mad", "iqr"])
        out_res = outliers(durations, method=method)

        col1, col2 = st.columns(2)
        col1.metric("Outlier Count", out_res["count"])
        col2.metric("Total Data Points", len(durations))

        if out_res["count"] > 0:
            st.warning(f"Detected {out_res['count']} anomalous data points:")
            outlier_df = pd.DataFrame(
                {
                    "Index": out_res["indices"],
                    "Value": out_res["outliers"],
                }
            )
            st.dataframe(outlier_df, use_container_width=True)
        else:
            st.success("No statistical outliers detected in the dataset.")
