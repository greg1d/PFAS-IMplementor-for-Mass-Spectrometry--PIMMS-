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


def plot_filtered_rt(adjusted_df, filtered_df, rt_eq, title="RT Filtering with Bounds"):
    plt.figure(figsize=(9, 6))

    # Recalculate the bounds using the equation
    log_mz = np.log(adjusted_df["m/z"])
    q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
    q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]

    # Identify excluded points
    mask = (adjusted_df["RT"] < q05) | (adjusted_df["RT"] > q95)
    excluded_df = adjusted_df[mask]

    # Plot included (filtered) points
    plt.scatter(
        filtered_df["m/z"],
        filtered_df["RT"],
        color="steelblue",
        alpha=0.6,
        edgecolors="k",
        s=30,
        label="Within Bounds",
    )

    # Plot excluded (outlier) points
    plt.scatter(
        excluded_df["m/z"],
        excluded_df["RT"],
        color="red",
        alpha=0.6,
        edgecolors="k",
        s=30,
        label="Outside Bounds",
    )

    # Sort x values for smooth line plotting
    mz_sorted = np.sort(adjusted_df["m/z"].values)
    ln_mz_sorted = np.log(mz_sorted)
    line_q05 = rt_eq["q05_slope"] * ln_mz_sorted + rt_eq["q05_intercept"]
    line_q95 = rt_eq["q95_slope"] * ln_mz_sorted + rt_eq["q95_intercept"]

    # Plot the quantile regression bounds
    plt.plot(mz_sorted, line_q05, color="black", linestyle="--", label="5th Percentile")
    plt.plot(
        mz_sorted, line_q95, color="black", linestyle="--", label="95th Percentile"
    )
    plt.fill_between(mz_sorted, line_q05, line_q95, color="gray", alpha=0.15)

    # Formatting
    plt.xlabel("m/z", fontsize=12, fontweight="bold", fontfamily="Arial")
    plt.ylabel(
        "Retention Time (min)", fontsize=12, fontweight="bold", fontfamily="Arial"
    )
    plt.title(title, fontsize=13, fontweight="bold", fontfamily="Arial")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
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
