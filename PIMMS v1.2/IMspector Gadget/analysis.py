import sys

import pandas as pd

# Ensure Python can find the module
sys.path.append(
    "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/PIMMS v1.2/IMspector Gadget"
)

# Import modules
from ccs_v_mz_library_search_modules.library_search_module import (
    count_external_library_matches_per_group,
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)
from rt_v_mz_library_search_modules.rt_v_mz_library_searcher import (
    split_mass_groups_by_groupid,
    rt_vs_mz_trend_analysis,
    refine_messy_rt_groups,
    combine_significant_groups,
    limit_consecutive_external_points,
    add_back_in_sample_intensities,
)


def run_analysis(adjusted_df, selected_repeating_units):
    """Runs CCS vs. m/z trend analysis pipeline."""

    print("[INFO] Starting mz_repeating_unit_analysis...")

    # ✅ Ensure selected_repeating_units is always a dictionary
    if not selected_repeating_units:
        print("[WARNING] No repeating units selected. Returning blank data.")
        return [], [], [], {}, pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    # ✅ Run analysis only if there are selected repeating units
    print(
        f"[DEBUG] Passing repeating units to mz_repeating_unit_analysis: {selected_repeating_units}"
    )
    mass_groups = mz_repeating_unit_analysis(adjusted_df, selected_repeating_units)

    if mass_groups is None or mass_groups.empty:
        print("[WARNING] No homologous series identified.")
        return [], [], [], {}, pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # ✅ Process CCS vs. m/z analysis
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

        # ✅ Append results
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


def run_library_search_analysis(selected_repeating_units):
    """
    Runs full pipeline for library search analysis.
    """

    print("[INFO] Running library search analysis...")

    # ✅ Step 1: Stack adjusted and library data
    stacked_df = stack_library_with_adjusted()

    # ✅ Perform Repeating Unit Analysis
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)
    if mass_groups.empty:
        return

    # ✅ Run CCS_v_mz_analysis and store IM groups
    filtered_IM_groups = []
    for group_id, group_df in mass_groups.groupby("GroupID"):
        IM_group, _, _, _ = CCS_v_mz_analysis(group_df)

        if IM_group:
            IM_group_df = group_df[
                group_df[["m/z", "CCS"]].apply(tuple, axis=1).isin(IM_group)
            ]

            # ✅ Filter IM groups using external standards check
            filtered_IM_group = count_external_library_matches_per_group(IM_group_df)
            print("filtered_IM_group", filtered_IM_group)
            filtered_IM_group = limit_consecutive_external_points(filtered_IM_group)
            if not filtered_IM_group.empty:
                filtered_IM_groups.append(filtered_IM_group)
    # ✅ Merge all valid IM groups into one DataFrame

    final_IM_group = (
        pd.concat(filtered_IM_groups, ignore_index=True)
        if filtered_IM_groups
        else pd.DataFrame()
    )
    print("final_IM_group", final_IM_group)
    return final_IM_group


def run_rt_mz_analysis(selected_repeating_units):
    """
    Compile analysis steps to generate the filtered_m_z_RT_groups DataFrame.
    """
    stacked_df = stack_library_with_adjusted()
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)
    split_mass_groups = split_mass_groups_by_groupid(mass_groups)
    sig_groups, messy_groups = rt_vs_mz_trend_analysis(split_mass_groups)
    refined_sig_groups, remaining_messy_groups = refine_messy_rt_groups(messy_groups)

    m_z_RT_groups = combine_significant_groups(sig_groups, refined_sig_groups)

    filtered_m_z_RT_groups = limit_consecutive_external_points(m_z_RT_groups)
    filtered_m_z_RT_groups = add_back_in_sample_intensities(
        stacked_df, filtered_m_z_RT_groups
    )
    return filtered_m_z_RT_groups
