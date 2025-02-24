import os
import sys

import matplotlib.pyplot as plt

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_library_search_modules.library_search_module import (
    get_library_path,
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.CCS_mz_trend_analysis import mz_repeating_unit_analysis

# ✅ Use dynamically selected library path
LIBRARY_PATH = get_library_path()
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
print("[INFO] Library path selected:", LIBRARY_PATH)

REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

# ✅ Select a subset of repeating units for analysis
SELECTED_UNITS = ["CF2"]
selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}

stacked_df = stack_library_with_adjusted()
mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)

import numpy as np
from scipy.stats import linregress


def RT_vs_mz_analysis(mass_groups):
    """
    Performs trend analysis on RT (Retention Time) vs m/z for each unique GroupID.
    - Excludes groups where a statistically significant trend is found (p < 0.05).
    - Fits a linear regression model for remaining groups.
    - Plots the RT vs m/z scatter along with the regression trend line.
    - Returns regression statistics for the included groups.

    Parameters:
    mass_groups (pd.DataFrame): DataFrame containing 'GroupID', 'RT', and 'm/z' columns.

    Returns:
    dict: Regression statistics (slope, intercept, R², p-value) for each included GroupID.
    """

    print("[DEBUG] Running RT_vs_mz_analysis...")

    # ✅ Check if required columns exist
    required_columns = {"GroupID", "RT", "m/z"}
    if not required_columns.issubset(mass_groups.columns):
        raise ValueError(f"[ERROR] DataFrame must contain {required_columns} columns.")

    # ✅ Get unique GroupIDs
    unique_groups = mass_groups["GroupID"].unique()
    print(f"[INFO] Identified {len(unique_groups)} unique GroupIDs for analysis.")

    # ✅ Store regression results
    regression_results = {}

    # ✅ Create plot
    plt.figure(figsize=(10, 6))

    # ✅ Perform trend analysis for each group
    for group in unique_groups:
        subset = mass_groups[mass_groups["GroupID"] == group]

        # ✅ Extract x (m/z) and y (RT)
        x = subset["m/z"].values
        y = subset["RT"].values

        if len(x) < 3:
            print(
                f"[WARNING] Group {group} has fewer than 3 points. Skipping trend analysis."
            )
            continue

        # ✅ Perform linear regression
        slope, intercept, r_value, p_value, _ = linregress(x, y)
        r_squared = r_value**2  # Compute R²

        # ✅ Filter out groups where p < 0.05
        if p_value > 0.05:
            print(
                f"[EXCLUDED] Group {group}: p-value = {p_value:.4g} (statistically insignificant, excluded)."
            )
            continue  # Skip plotting & saving this group

        # ✅ Store regression stats only for included groups
        regression_results[group] = {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "p_value": p_value,
        }

        print(
            f"[DEBUG] Group {group}: slope={slope:.4f}, R²={r_squared:.4f}, p={p_value:.4g} (included)."
        )

        # ✅ Scatter plot of actual data
        plt.scatter(x, y, label=f"Group {group}", alpha=0.7)

        # ✅ Plot regression line
        x_range = np.linspace(min(x), max(x), 100)
        y_fit = slope * x_range + intercept
        plt.plot(x_range, y_fit, linestyle="--", linewidth=2)

    # ✅ Customize plot
    plt.xlabel("m/z")
    plt.ylabel("RT (Retention Time)")
    plt.title("RT vs m/z Trend Analysis (Filtered)")
    plt.legend()
    plt.grid(True)

    # ✅ Show plot
    plt.show()

    print("[INFO] RT vs m/z analysis completed successfully.")
    return regression_results  # ✅ Return regression stats for external use


# ✅ Example Usage:
regression_results = RT_vs_mz_analysis(mass_groups)
print(regression_results)
