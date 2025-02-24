import os
import sys


# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_library_search_modules.library_search_module import (
    get_library_path,
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.CCS_mz_trend_analysis import mz_repeating_unit_analysis

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

# ✅ Use dynamically selected library path
LIBRARY_PATH = get_library_path()
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
print("[INFO] Library path selected:", LIBRARY_PATH)

stacked_df = stack_library_with_adjusted()
print(stacked_df)
mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)


def rt_v_mz_trend_analysis(mass_groups):
    """
    Performs RT vs. m/z trend analysis by grouping data based on 'GroupID'.

    Args:
        mass_groups (pd.DataFrame): DataFrame containing homologous series data.

    Returns:
        dict: A dictionary with GroupID as keys and DataFrames with RT and m/z as values.
    """

    # ✅ Ensure DataFrame is valid
    if mass_groups is None or mass_groups.empty:
        print("[ERROR] `mass_groups` is empty or None. Exiting RT vs. m/z analysis.")
        return {}

    # ✅ Extract only relevant columns
    grouped_rt_mz = {}

    print(
        f"[INFO] Running RT vs. m/z analysis on {mass_groups['GroupID'].nunique()} groups."
    )

    for group_id, group_df in mass_groups.groupby("GroupID"):
        # ✅ Extract RT and m/z for the current GroupID
        rt_mz_df = group_df[["RT", "m/z"]].copy()

        # ✅ Store in dictionary
        grouped_rt_mz[group_id] = rt_mz_df

        # ✅ Debugging Output
        print(f"[DEBUG] Processed GroupID {group_id} with {len(rt_mz_df)} points.")
        print(rt_mz_df.head(), "\n")

    return grouped_rt_mz  # ✅ Return grouped data for further analysis


rt_mz_results = rt_v_mz_trend_analysis(mass_groups)
print(rt_mz_results)
