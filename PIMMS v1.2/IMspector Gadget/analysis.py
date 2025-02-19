import os
import sys

import pandas as pd

# Ensure Python can find the module
sys.path.append(
    "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/PIMMS v1.2/IMspector Gadget"
)

# Import modules
from ccs_v_mz_library_search_modules.library_search_module import (
    external_mz_library_matching,
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)
from config import LIBRARY_PATH


def run_analysis(adjusted_df):
    """Runs CCS vs. m/z trend analysis pipeline."""
    print("[INFO] Starting mz_repeating_unit_analysis...")

    # Identify homologous series
    mass_groups = mz_repeating_unit_analysis(adjusted_df)

    if mass_groups is None or mass_groups.empty:
        print(
            "[WARNING] No homologous series identified. Continuing with blank analysis."
        )

        # ✅ Return a DataFrame with at least the required column
        mass_groups = pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

        return [], [], [], {}, mass_groups  # ✅ Ensure valid return structure

    # ✅ Ensure "GroupID" exists before further processing
    if "GroupID" not in mass_groups.columns:
        print(
            "[ERROR] Missing 'GroupID' column in mass_groups. Creating an empty column."
        )
        mass_groups["GroupID"] = pd.Series(dtype="str")  # ✅ Add an empty column

    # ✅ Debugging before proceeding
    print(f"[DEBUG] mass_groups structure: {mass_groups.dtypes}")
    print(f"[DEBUG] mass_groups.head():\n{mass_groups.head()}")

    # ✅ Now it's safe to access "GroupID"
    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # Perform CCS vs. m/z analysis
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
    mass_only_groups = {}

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")

    for idx, (group_id, group_df) in enumerate(
        mass_groups.groupby("GroupID", dropna=True)
    ):
        print(f"[DEBUG] Analyzing Group {idx + 1} (GroupID: {group_id})")

        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # Append results for plotting
        refined_groups.append(IM_group)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)

        if mass_only_group:
            mass_only_groups[f"Group {idx + 1}"] = mass_only_group

    return (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )


def run_library_search_analysis():
    """
    Runs the full pipeline for library search analysis:
    1. Stacks adjusted_df and library_df.
    2. Performs homologous series identification.
    3. Runs CCS vs. m/z analysis.
    4. Filters homologous series using external library matching criteria.

    Returns:
        - filtered_IM_group (pd.DataFrame): The final set of valid homologous series.
        - stacked_df (pd.DataFrame): The combined dataset of adjusted and library features.
    """

    print("[INFO] Running library search analysis...")

    # ✅ Step 1: Stack adjusted and library data
    stacked_df = stack_library_with_adjusted()
    if stacked_df is None or stacked_df.empty:
        print("[WARNING] Stacked dataset is empty. Exiting analysis.")
        return None, None

    print(
        f"[DEBUG] Stacked dataset loaded successfully with {len(stacked_df)} rows and {len(stacked_df.columns)} columns."
    )

    # ✅ Extract library name for matching
    library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

    # ✅ Step 2: Identify homologous series using repeating unit analysis
    print("[INFO] Running mz_repeating_unit_analysis...")
    mass_groups = mz_repeating_unit_analysis(stacked_df)

    if mass_groups.empty:
        print("[WARNING] No homologous series identified.")
        return None, stacked_df

    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # ✅ Step 3: Run CCS vs. m/z analysis for each group
    filtered_IM_groups = []
    for group_id, group_df in mass_groups.groupby("GroupID"):
        print(f"[INFO] Processing GroupID {group_id}...")
        IM_group, _, _, _ = CCS_v_mz_analysis(group_df)

        if IM_group:
            IM_group_df = group_df[
                group_df[["m/z", "CCS"]].apply(tuple, axis=1).isin(IM_group)
            ]

            # ✅ Step 4: Filter homologous series using external library matching
            filtered_IM_group = external_mz_library_matching(
                IM_group_df, library_match_source
            )

            if not filtered_IM_group.empty:
                filtered_IM_groups.append(filtered_IM_group)

    # ✅ Merge all valid IM groups into one DataFrame
    final_IM_group = (
        pd.concat(filtered_IM_groups, ignore_index=True)
        if filtered_IM_groups
        else pd.DataFrame()
    )

    print(
        f"[INFO] Library search analysis completed. {len(final_IM_group)} valid homologous series found."
    )

    return final_IM_group, stacked_df
