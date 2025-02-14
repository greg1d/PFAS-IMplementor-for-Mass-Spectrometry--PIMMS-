from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)
from config import REPEATING_UNITS


def run_analysis(adjusted_df):
    """Runs CCS vs. m/z trend analysis pipeline."""
    print("[INFO] Starting mz_repeating_unit_analysis...")

    # Identify homologous series
    mass_groups = mz_repeating_unit_analysis(adjusted_df, REPEATING_UNITS)

    if mass_groups.empty:
        print("[WARNING] No homologous series identified.")
        return [], [], [], {}, mass_groups

    # Perform CCS vs. m/z analysis
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
    mass_only_groups = {}

    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        refined_data, post_decay, branched_isomer, mass_only_group = CCS_v_mz_analysis(
            group_df
        )

        if refined_data:
            refined_groups.append(refined_data)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_decay)

        if mass_only_group:
            mass_only_groups[f"Group {idx + 1}"] = mass_only_group

    return (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )
