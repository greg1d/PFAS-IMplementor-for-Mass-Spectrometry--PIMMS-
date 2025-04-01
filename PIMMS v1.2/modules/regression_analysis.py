import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Append the path to the 'CCSRT v mz predictions' folder
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "CCSRT v mz predictions")
)
if module_path not in sys.path:
    sys.path.append(module_path)

# Import your model functions
from quantile_regression_model_CCS import run_CCS_regression_analysis
from quantile_regression_model_RT import run_RT_regression_analysis


def exclude_rt_values(adjusted_df, rt_eq):
    """
    Exclude rows where RT is outside the 5th–95th percentile range
    defined by log(m/z) regression equations.

    Parameters:
        adjusted_df (pd.DataFrame): Must include 'm/z' and 'RT' columns.
        rt_eq (dict): Dictionary with 'q05_slope', 'q05_intercept', 'q95_slope', 'q95_intercept'.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    log_mz = np.log(adjusted_df["m/z"])

    q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
    q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]

    filtered = adjusted_df[
        (adjusted_df["RT"] >= q05) & (adjusted_df["RT"] <= q95)
    ].copy()
    return filtered


def plot_filtered_rt(
    adjusted_df, filtered_df, rt_eq, title="Filtered RT with Quantile Bounds"
):
    # Recalculate bounds
    log_mz = np.log(adjusted_df["m/z"])
    q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
    q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]

    # Identify outliers
    mask = (adjusted_df["RT"] < q05) | (adjusted_df["RT"] > q95)
    excluded_df = adjusted_df[mask]

    # Prepare for line plotting
    mz_sorted = np.sort(adjusted_df["m/z"].values)
    ln_mz_sorted = np.log(mz_sorted)
    line_q05 = rt_eq["q05_slope"] * ln_mz_sorted + rt_eq["q05_intercept"]
    line_q95 = rt_eq["q95_slope"] * ln_mz_sorted + rt_eq["q95_intercept"]

    # Start plot
    fig, ax = plt.subplots(figsize=(7, 5))

    # Plot inliers
    ax.scatter(
        filtered_df["m/z"],
        filtered_df["RT"],
        color="gray",
        alpha=0.3,
        s=15,
        label="Within Bounds",
    )

    # Plot outliers
    ax.scatter(
        excluded_df["m/z"],
        excluded_df["RT"],
        color="red",
        alpha=0.6,
        edgecolors="k",
        s=30,
        label="Outside Bounds",
    )

    # Plot quantile lines and band
    ax.plot(mz_sorted, line_q05, linestyle="--", color="red", label="5th Percentile")
    ax.plot(mz_sorted, line_q95, linestyle="--", color="red", label="95th Percentile")
    ax.fill_between(mz_sorted, line_q05, line_q95, color="red", alpha=0.1)

    # Axis labels, limits, and ticks
    ax.set_title(title, fontsize=10, fontweight="bold", fontfamily="Arial")
    ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontfamily="Arial")
    ax.set_ylabel(
        "Retention Time (min)", fontsize=10, fontweight="bold", fontfamily="Arial"
    )
    ax.set_ylim(0, 20)
    ax.grid(True)
    ax.tick_params(axis="both", labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname("Arial")
        label.set_fontweight("bold")

    # Styled legend
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    legend = ax.legend(
        unique.values(),
        unique.keys(),
        loc="upper left",
        fontsize=8,
        frameon=True,
        fancybox=True,
        facecolor="white",
        edgecolor="gray",
        framealpha=0.7,
    )
    for text in legend.get_texts():
        text.set_fontweight("bold")
        text.set_fontfamily("Arial")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


def main():
    # File paths
    library_file = (
        r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
    )
    # Run quantile regression on CCS (doesn't need to return anything for this use case)
    print("\nRunning Quantile Regression on CCS...")
    ccs_eq = run_CCS_regression_analysis(library_file)
    print(ccs_eq)
    RT_eq = run_RT_regression_analysis(library_file)
    print(RT_eq)
    adjusted_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(adjusted_path)

    filtered_df = exclude_rt_values(adjusted_df, RT_eq)
    print(filtered_df)
    plot_filtered_rt(adjusted_df, filtered_df, RT_eq)


if __name__ == "__main__":
    main()
