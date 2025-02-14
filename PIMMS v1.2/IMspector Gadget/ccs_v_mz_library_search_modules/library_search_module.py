import os
import sys

import pandas as pd

# Get the absolute path of the "IMspector Gadget" directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.append(base_dir)  # Add base dir to Python path


from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)

# ✅ Hardcoded file path to the dataset
FILE_PATH = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"

# ✅ Hardcoded repeating units (Modify as needed)
REPEATING_UNITS = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]


def main():
    """Perform trend analysis on the dataset, similar to the existing main function."""

    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] File not found: {FILE_PATH}")
        return

    # ✅ Load dataset (Same as in main function)
    try:
        adjusted_df = pd.read_csv(FILE_PATH)
        print(f"[INFO] Loaded data with shape: {adjusted_df.shape}")
    except Exception as e:
        print(f"[ERROR] Failed to read file. Ensure it's a valid CSV. Error: {e}")
        return

    print("\n[INFO] Starting mz_repeating_unit_analysis...")

    # ✅ Step 1: Identify homologous series
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=REPEATING_UNITS
    )

    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups identified. Exiting.")
        return

    print(f"[DEBUG] Identified {len(mass_groups)} homologous series.")

    # ✅ Step 2: Perform CCS vs. m/z analysis
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
    mass_only_groups = {}

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")
    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        print(f"[DEBUG] Analyzing Group {idx + 1} (GroupID: {group_id})")

        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # ✅ Store results for further use
        refined_groups.append(IM_group)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)

        if isinstance(mass_only_group, list) and len(mass_only_group) > 0:
            mass_only_groups[f"Group {idx + 1}"] = mass_only_group

    # ✅ Step 3: Print Debugging Before Plotting
    print("\n[INFO] Final Data Sent to Plot:")
    print(f"  - IM Groups: {sum(len(group) for group in refined_groups)} points")
    print(
        f"  - Branched Isomers: {sum(len(group) for group in branched_isomer_groups)} points"
    )
    print(
        f"  - Post Source Decay: {sum(len(group) for group in post_source_decay_groups)} points"
    )
    print(
        f"  - Mass-Only Groups: {sum(len(group) for group in mass_only_groups.values())} points"
    )

    # ✅ Step 4: Return Processed Data
    return (
        adjusted_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )


if __name__ == "__main__":
    results = main()
