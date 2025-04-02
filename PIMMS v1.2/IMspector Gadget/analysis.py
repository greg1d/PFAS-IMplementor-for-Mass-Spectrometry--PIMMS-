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
from rt_v_mz_library_search_modules.rt_v_mz_library_searcher import (
    add_back_in_sample_intensities,
    combine_significant_groups,
    limit_consecutive_external_points,
    refine_messy_rt_groups,
    rt_vs_mz_trend_analysis,
    split_mass_groups_by_groupid,
)


def run_analysis(adjusted_df, selected_repeating_units):
    """Runs CCS vs. m/z trend analysis pipeline."""

    # ✅ Ensure selected_repeating_units is always a dictionary
    if not selected_repeating_units:
        return [], [], [], {}, pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    mass_groups = mz_repeating_unit_analysis(adjusted_df, selected_repeating_units)

    if mass_groups is None or mass_groups.empty:
        return [], [], [], {}, pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    # ✅ Process CCS vs. m/z analysis
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []

    for idx, (group_id, group_df) in enumerate(
        mass_groups.groupby("GroupID", dropna=True)
    ):
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # ✅ Append results
        refined_groups.append(IM_group)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)

    return (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_groups,
    )


def run_library_search_analysis(selected_repeating_units):
    """
    Runs full pipeline for library search analysis.
    """

    # ✅ Step 1: Stack adjusted and library data
    stacked_df = stack_library_with_adjusted()
    if stacked_df is None or stacked_df.empty:
        return None, None
    # ✅ Extract library name
    library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

    # ✅ Step 2: Identify homologous series using user-selected repeating units
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)

    if mass_groups.empty:
        return None, stacked_df

    # ✅ Step 3: Run CCS vs. m/z analysis
    filtered_IM_groups = []
    for group_id, group_df in mass_groups.groupby("GroupID"):
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

    # ✅ Merge valid IM groups into one DataFrame
    final_IM_group = (
        pd.concat(filtered_IM_groups, ignore_index=True)
        if filtered_IM_groups
        else pd.DataFrame()
    )

    return final_IM_group, stacked_df


def run_rt_mz_analysis(selected_repeating_units):
    """
    Compile analysis steps to generate the filtered_m_z_RT_groups DataFrame.
    """
    stacked_df = stack_library_with_adjusted()
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)
    split_mass_groups = split_mass_groups_by_groupid(mass_groups)
    sig_groups, messy_groups = rt_vs_mz_trend_analysis(split_mass_groups)
    refined_sig_groups = refine_messy_rt_groups(messy_groups)

    m_z_RT_groups = combine_significant_groups(sig_groups, refined_sig_groups)

    filtered_m_z_RT_groups = limit_consecutive_external_points(m_z_RT_groups)
    filtered_m_z_RT_groups = add_back_in_sample_intensities(
        stacked_df, filtered_m_z_RT_groups
    )
    return filtered_m_z_RT_groups


def main():
    run_rt_mz_analysis(selected_repeating_units={"CF2": 49.9969064})


if __name__ == "__main__":
    main()
