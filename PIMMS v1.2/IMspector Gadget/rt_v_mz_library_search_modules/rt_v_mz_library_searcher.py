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
print(mass_groups)


def RT_vs_mz_analysis(mass_groups):
    """
    Plots the RT (Retention Time) vs m/z for each unique GroupID in the mass_groups DataFrame.

    Parameters:
    mass_groups (pd.DataFrame): DataFrame containing 'GroupID', 'RT', and 'm/z' columns.
    """
    # Check if required columns exist
    if not {"GroupID", "RT", "m/z"}.issubset(mass_groups.columns):
        raise ValueError("DataFrame must contain 'GroupID', 'RT', and 'm/z' columns")

    # Get unique GroupIDs
    unique_groups = mass_groups["GroupID"].unique()

    # Create plot
    plt.figure(figsize=(10, 6))

    # Plot each group separately
    for group in unique_groups:
        subset = mass_groups[mass_groups["GroupID"] == group]
        plt.scatter(subset["m/z"], subset["RT"], label=f"Group {group}", alpha=0.7)

    # Customize plot
    plt.xlabel("m/z")
    plt.ylabel("RT (Retention Time)")
    plt.title("RT vs m/z for each GroupID")
    plt.legend()
    plt.grid(True)

    # Show plot
    plt.show()


RT_vs_mz_analysis(mass_groups)
