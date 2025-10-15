import bisect


def calculate_mass_error(mass, mass_error_ppm=10, z=1):
    """Calculate the absolute mass error based on ppm."""
    mass_error = mass * mass_error_ppm * 1e-6
    return mass_error / z


def find_peaks_within_bounds(array, z, M, i, mass_error_ppm=10):
    """Finds peaks within the mass error bounds using binary search."""
    mass_bound = calculate_mass_error(array[i], mass_error_ppm, z)
    lower_bound = array[i] + (M / z) - mass_bound
    upper_bound = array[i] + (M / z) + mass_bound
    j_start = bisect.bisect_left(array, lower_bound, i + 1)
    j_end = bisect.bisect_right(array, upper_bound, i + 1)
    return array[j_start:j_end], j_end - j_start


def expand_group(
    adjusted_df,
    initial_peak,
    initial_rt,
    initial_ccs,
    z_range,
    mass_error_ppm=10,
    rt_tolerance=0.5,
    ccs_tolerance=2.0,
):
    """Expands a group of related isotopic peaks from an initial seed peak."""
    array = adjusted_df["m/z"].tolist()
    rt_array = adjusted_df["RT"].tolist()
    ccs_array = adjusted_df["CCS"].tolist()

    group = [initial_peak]
    identified_features = set(group)
    to_process = [initial_peak]

    while to_process:
        current_peak = to_process.pop(0)
        current_idx = array.index(current_peak)
        current_rt = rt_array[current_idx]
        current_ccs = ccs_array[current_idx]

        for z in z_range:
            peaks, _ = find_peaks_within_bounds(
                array, z, 1, current_idx, mass_error_ppm
            )
            for peak in peaks:
                idx = array.index(peak)
                if (
                    peak not in identified_features
                    and abs(rt_array[idx] - current_rt) <= rt_tolerance
                    and abs(ccs_array[idx] - current_ccs) / current_ccs * 100
                    <= ccs_tolerance
                ):
                    identified_features.add(peak)
                    group.append(peak)
                    to_process.append(peak)
    return group


def analyze_adjusted_df(
    adjusted_df,
    z_range=range(1, 4),
):
    mass_error_ppm = 1
    rt_tolerance = 0.5
    ccs_tolerance = 0.5
    """
    Iterates through a DataFrame to find and group related isotopic features.
    """
    # Gracefully handle empty inputs
    if adjusted_df.empty:
        return []

    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)
    array = adjusted_df["m/z"].tolist()

    identified_features = set()
    groups = []

    for i in range(len(array)):
        if array[i] not in identified_features:
            group = expand_group(
                adjusted_df,
                array[i],
                adjusted_df["RT"].iloc[i],
                adjusted_df["CCS"].iloc[i],
                z_range,
                mass_error_ppm,
                rt_tolerance,
                ccs_tolerance,
            )
            if len(group) > 1:
                groups.append(group)
                identified_features.update(group)

    return groups


def merge_groups_into_adjusted_df(adjusted_df, groups):
    """
    Merges identified groups back into the DataFrame, keeping the feature with
    the lowest m/z as the representative for each group.
    """
    # Gracefully handle empty inputs
    if adjusted_df.empty or not groups:
        return adjusted_df

    # Identify intensity columns (assumed to be non-metadata)
    intensity_columns = [
        col
        for col in adjusted_df.columns
        if col not in ["ID", "RT", "DT", "CCS", "m/z"]
    ]

    for group in groups:
        # Find all rows in the DataFrame that correspond to the current group
        group_df = adjusted_df[adjusted_df["m/z"].isin(group)]

        # Skip if the group is somehow not in the DataFrame
        if group_df.empty:
            continue

        # Identify the representative row (the one with the lowest m/z)
        representative_row = group_df.loc[group_df["m/z"].idxmin()]
        representative_mz = representative_row["m/z"]

        # Set intensity columns of other rows in the group to match the representative row
        for col in intensity_columns:
            adjusted_df.loc[adjusted_df["m/z"].isin(group), col] = representative_row[
                col
            ]

        # Identify m/z values to remove (all except the representative one)
        mz_to_remove = [mz for mz in group if mz != representative_mz]

        # Remove the non-representative rows from the DataFrame
        if mz_to_remove:
            adjusted_df = adjusted_df[~adjusted_df["m/z"].isin(mz_to_remove)]

    return adjusted_df.reset_index(drop=True)
