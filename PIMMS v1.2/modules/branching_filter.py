import pandas as pd


import numpy as np


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


def group_by_mz_ppm(adjusted_df, mass_error_ppm=10):
    """
    Vectorized m/z grouping using sorted array and np.searchsorted.
    """
    mz_sorted_idx = np.argsort(adjusted_df["m/z"].values)
    mz_sorted = adjusted_df["m/z"].values[mz_sorted_idx]
    used = np.zeros(len(mz_sorted), dtype=bool)

    groups = []
    for i, mz in enumerate(mz_sorted):
        if used[i]:
            continue
        mass_bound = calculate_mass_error_no_charge(mz, mass_error_ppm)
        lower = mz - mass_bound
        upper = mz + mass_bound

        # indices within ±ppm
        j_start = np.searchsorted(mz_sorted, lower, side="left")
        j_end = np.searchsorted(mz_sorted, upper, side="right")
        idx_group = np.arange(j_start, j_end)
        idx_group = idx_group[~used[idx_group]]

        if len(idx_group) > 0:
            groups.append(adjusted_df.iloc[mz_sorted_idx[idx_group]].copy())
            used[idx_group] = True

    return groups


def split_by_tolerance(df, col, tolerance, percent=False):
    """
    Vectorized splitting of a sorted DataFrame by tolerance.
    If percent=True, tolerance is a percentage of the min value in the group.
    Returns a list of DataFrames.
    """
    arr = df[col].values
    n = len(arr)
    if n == 0:
        return []

    split_indices = []
    start_idx = 0

    while start_idx < n:
        if percent:
            min_val = arr[start_idx]
            mask = np.where((arr[start_idx:] - min_val) / min_val * 100 <= tolerance)[0]
        else:
            min_val = arr[start_idx]
            mask = np.where((arr[start_idx:] - min_val) <= tolerance)[0]

        if len(mask) == 0:
            end_idx = start_idx
        else:
            end_idx = start_idx + mask[-1] + 1

        split_indices.append((start_idx, end_idx))
        start_idx = end_idx

    # Build sub-DataFrames
    return [df.iloc[start:end].copy() for start, end in split_indices]


def optimal_ccs_grouping(group_dfs, ccs_tolerance=2.0):
    final_groups = []
    for group_df in group_dfs:
        group_sorted = group_df.sort_values("CCS").reset_index(drop=True)
        ccs = group_sorted["CCS"].values

        # Vectorized approach
        start_idx = 0
        n = len(ccs)
        while start_idx < n:
            min_ccs = ccs[start_idx]
            # find the furthest index where % tolerance is not exceeded
            end_idx = start_idx + np.searchsorted(
                ccs[start_idx:], min_ccs * (1 + ccs_tolerance / 100), side="right"
            )
            final_groups.append(group_sorted.iloc[start_idx:end_idx].copy())
            start_idx = end_idx

    return final_groups


def optimal_rt_grouping(group_dfs, rt_tolerance=0.5):
    final_groups = []
    for group_df in group_dfs:
        group_sorted = group_df.sort_values("RT").reset_index(drop=True)
        rt = group_sorted["RT"].values

        # Vectorized approach
        start_idx = 0
        n = len(rt)
        while start_idx < n:
            rt_min = rt[start_idx]
            # find the furthest index within tolerance
            end_idx = start_idx + np.searchsorted(
                rt[start_idx:], rt_min + rt_tolerance, side="right"
            )
            final_groups.append(group_sorted.iloc[start_idx:end_idx].copy())
            start_idx = end_idx

    return final_groups


def branching_analyze(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    print("[Stage 1] Grouping by m/z...")
    mz_groups = group_by_mz_ppm(adjusted_df, mass_error_ppm)
    print(f"[INFO] m/z groups found: {len(mz_groups)}")

    print("[Stage 2] Refining groups by CCS tolerance...")
    ccs_groups = optimal_ccs_grouping(mz_groups, ccs_tolerance)
    print(f"[INFO] CCS-refined groups: {len(ccs_groups)}")

    print("[Stage 3] Refining groups by RT tolerance...")
    rt_groups = optimal_rt_grouping(ccs_groups, rt_tolerance)
    print(f"[INFO] RT-refined groups: {len(rt_groups)}")

    return rt_groups


def branching_merge(group_dfs, original_df, metadata_cols):
    """
    [CORRECTED] For each group DataFrame, merge and summarize features.
    Identifies sample columns by excluding metadata columns.
    """
    # --- Guard Clause for empty list of groups ---
    if not group_dfs:
        print("[INFO] No groups to merge. Returning a structured empty DataFrame.")
        # Determine final columns from the original DataFrame and metadata list
        output_metadata = ["ID", "RT", "DT", "CCS", "m/z"]
        # The sample columns are all columns from original_df that are not metadata
        sample_cols = [col for col in original_df.columns if col not in metadata_cols]
        # Ensure the final columns only contain metadata that actually exists
        present_output_metadata = [
            c for c in output_metadata if c in original_df.columns
        ]
        final_cols = present_output_metadata + sample_cols
        return pd.DataFrame(columns=final_cols)

    summaries = []
    for idx, group in enumerate(group_dfs, 1):
        # This summary logic for metadata is fine
        summary = {
            "ID": group.loc[group.index[0], "ID"],
            "RT": group["RT"].mean(),
            "DT": group["DT"].mean() if "DT" in group.columns else None,
            "CCS": group["CCS"].mean(),
            "m/z": group["m/z"].mean(),
        }

        # --- THE FIX: Identify sample columns by EXCLUSION, not by '.d' ---
        sample_cols = [col for col in group.columns if col not in metadata_cols]
        for col in sample_cols:
            summary[col] = group[col].max()

        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)

    # Robust column reordering remains the same
    fixed_cols = ["ID", "RT", "DT", "CCS", "m/z"]
    present_fixed_cols = [c for c in fixed_cols if c in summary_df.columns]
    other_cols = [col for col in summary_df.columns if col not in present_fixed_cols]

    return summary_df[present_fixed_cols + other_cols]
