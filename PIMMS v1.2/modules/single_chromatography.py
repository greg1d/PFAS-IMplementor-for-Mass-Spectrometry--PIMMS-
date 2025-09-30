import bisect
import numpy as np


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, mass, mass_error_ppm):
    """Finds peaks within the mass error bounds using binary search."""
    mass_bound = calculate_mass_error_no_charge(mass, mass_error_ppm)
    lower_bound = mass - mass_bound
    upper_bound = mass + mass_bound

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    return array[j_start:j_end]


def prescreen_by_ccs(adjusted_df, library_df, mass_error_ppm):
    """
    From adjusted_df, select features not classified as 'likely'.
    Remove points that have CCS higher than 1.03 * any matching m/z entry in library_df (within ppm).
    Returns adjusted_df with these points excluded.
    """
    # Identify the non-"likely" features for screening
    other_df = adjusted_df[adjusted_df["Classification Type"] != "likely"].copy()
    mz_library = library_df["m/z"].values
    ccs_library = library_df["CCS"].values

    # Track indices to exclude
    indices_to_exclude = []

    for idx, row in other_df.iterrows():
        mz_other = row["m/z"]
        ccs_other = row["CCS"]

        # Calculate ppm window
        ppm_tol = mz_other * mass_error_ppm * 1e-6
        lower_mz = mz_other - ppm_tol
        upper_mz = mz_other + ppm_tol

        # Find matching m/z entries in the library
        match_mask = (mz_library >= lower_mz) & (mz_library <= upper_mz)
        matching_ccs = ccs_library[match_mask]

        # Mark for exclusion if CCS is too high
        if matching_ccs.size > 0 and ccs_other > 1.03 * matching_ccs.max():
            indices_to_exclude.append(idx)
    # Drop rows with high CCS
    adjusted_df_filtered = adjusted_df.drop(index=indices_to_exclude).copy()
    print(f"✔️ CCS prescreening applied: removed {len(indices_to_exclude)}")
    return adjusted_df_filtered


def group_and_eliminate(adjusted_df, mass_error_ppm):
    """
    Identify m/z groups within ±ppm, and remove any group that:
    - has >=2 features,
    - has RT spread > 2 min,
    - has CCS spread > 15%.
    Returns the filtered adjusted_df.
    """
    mz_array = sorted(adjusted_df["m/z"].dropna())
    used = set()
    indices_to_remove = set()

    for mz in mz_array:
        if mz in used:
            continue

        group_mz = find_similar_peaks(mz_array, mz, mass_error_ppm)
        group_mz = [val for val in group_mz if val not in used]

        if len(group_mz) >= 2:
            group_df = adjusted_df[adjusted_df["m/z"].isin(group_mz)].copy()
            rt_min = group_df["RT"].min()
            rt_max = group_df["RT"].max()
            rt_spread = rt_max - rt_min

            ccs_min = group_df["CCS"].min()
            ccs_max = group_df["CCS"].max()
            ccs_spread_pct = (
                100 * (ccs_max - ccs_min) / ccs_min if ccs_min > 0 else np.inf
            )

            if rt_spread > 1.0 or ccs_spread_pct > 15.0:
                indices_to_remove.update(group_df.index)

            used.update(group_mz)

    # Drop excluded group features from adjusted_df
    filtered_df = adjusted_df.drop(index=indices_to_remove).copy()
    print(f"✔️ Group elimination applied: removed {len(indices_to_remove)}")

    return filtered_df


def unsaturated_chain_elimination(adjusted_df, mass_error_ppm=15):
    """
    Removes features matching the CnF2n-1 pattern: exact mass = 12*n_C + 18.9984032*(2*n_C - 1)

    Parameters:
        adjusted_df: DataFrame containing mass values with column 'm/z'
        mass_error_ppm: ppm tolerance to match theoretical formula mass

    Returns:
        Filtered DataFrame with CnF2n-1 matches removed
    """
    F = 18.9984032
    C = 12.0000000

    to_exclude = set()

    for n_C in range(1, 40):  # reasonable carbon range
        formula_mass = C * n_C + F * (2 * n_C - 1)
        ppm_tol = formula_mass * mass_error_ppm * 1e-6
        lower = formula_mass - ppm_tol
        upper = formula_mass + ppm_tol

        # Find all rows where mass is within the ppm window
        matches = adjusted_df[
            (adjusted_df["m/z"] >= lower) & (adjusted_df["m/z"] <= upper)
        ]
        if not matches.empty:
            to_exclude.update(matches.index)
    print(f"✔️ after unsaturated chain elimination: removed {len(to_exclude)}")

    return adjusted_df.drop(index=to_exclude).reset_index(drop=True)


def combined_filter_pipeline(adjusted_df, library_df, mass_error_ppm=15):
    if adjusted_df.empty:
        print("[INFO] No features to process for filtering pipeline.")
        return adjusted_df
    adjusted_df = prescreen_by_ccs(adjusted_df, library_df, mass_error_ppm)
    adjusted_df = group_and_eliminate(adjusted_df, mass_error_ppm)
    adjusted_df = unsaturated_chain_elimination(adjusted_df, mass_error_ppm)
    return adjusted_df
