import os
import sys
from scipy.stats import linregress
import pandas as pd

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


def split_mass_groups_by_groupid(mass_groups):
    """
    Splits the mass_groups DataFrame into separate DataFrames for each unique GroupID.

    Args:
        mass_groups (pd.DataFrame): DataFrame containing 'GroupID' column.

    Returns:
        dict: A dictionary where keys are GroupIDs and values are the corresponding DataFrames.
    """

    if "GroupID" not in mass_groups.columns:
        raise ValueError("[ERROR] DataFrame must contain 'GroupID' column.")

    # ✅ Group by 'GroupID' and store each subset in a dictionary
    split_mass_groups = {group: df for group, df in mass_groups.groupby("GroupID")}

    # ✅ Debugging: Print each group separately
    for group_id, df in split_mass_groups.items():
        print(f"\n[DEBUG] Group {group_id} (n={len(df)}):")
        print(df.to_string(index=False))  # Print full DataFrame for clarity

    return split_mass_groups


def rt_vs_mz_trend_analysis(split_mass_groups):
    """
    Performs trend analysis on RT (Retention Time) vs m/z for each unique GroupID.
    - Categorizes groups into 'significant_RT_group' (p < 0.05) and 'messy_RT_group' (p ≥ 0.05).
    - Returns these two DataFrames separately.

    Args:
        split_mass_groups (dict): Dictionary of DataFrames split by GroupID.

    Returns:
        significant_RT_group (pd.DataFrame): Groups with significant trends (p < 0.05).
        messy_RT_group (pd.DataFrame): Groups with non-significant trends (p ≥ 0.05).
    """

    print("\n[INFO] Running RT vs m/z Trend Analysis...")

    significant_RT_groups = []  # ✅ Store significant groups
    messy_RT_groups = []  # ✅ Store messy groups

    for group_id, df in split_mass_groups.items():
        print(f"\n[DEBUG] Processing Group {group_id}...")

        if df.shape[0] < 3:
            print(f"[WARNING] Group {group_id} has fewer than 3 points. Skipping.")
            continue

        # ✅ Extract x (m/z) and y (RT)
        x = df["m/z"].values
        y = df["RT"].values

        # ✅ Perform linear regression
        slope, intercept, r_value, p_value, _ = linregress(x, y)
        r_squared = r_value**2  # Compute R²

        print(
            f"[DEBUG] Group {group_id}: slope={slope:.4f}, R²={r_squared:.4f}, p={p_value:.4g}"
        )

        # ✅ Categorize groups based on p-value
        if p_value < 0.05:
            significant_RT_groups.append(df)  # Store significant group
        else:
            messy_RT_groups.append(df)  # Store messy group

    # ✅ Convert lists to DataFrames
    significant_RT_group = (
        pd.concat(significant_RT_groups, ignore_index=True)
        if significant_RT_groups
        else pd.DataFrame()
    )
    messy_RT_group = (
        pd.concat(messy_RT_groups, ignore_index=True)
        if messy_RT_groups
        else pd.DataFrame()
    )

    print("\n[INFO] RT vs m/z trend analysis completed.")
    print(f"[INFO] Significant RT Groups: {len(significant_RT_group)} rows.")
    print(f"[INFO] Messy RT Groups: {len(messy_RT_group)} rows.")

    return significant_RT_group, messy_RT_group


split_mass_groups = split_mass_groups_by_groupid(mass_groups)
sig_groups, messy_groups = rt_vs_mz_trend_analysis(split_mass_groups)
# Print results
print("\n[INFO] Significant RT Groups:")
print(sig_groups)

print("\n[INFO] Messy RT Groups:")
print(messy_groups)
