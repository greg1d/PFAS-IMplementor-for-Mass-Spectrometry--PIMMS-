import bisect


def calculate_mass_error(mass, mass_error_ppm=10, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    return mass_error / z


def find_peaks_within_bounds(array, z, M, i, mass_error_ppm=10):
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
    mass_error_ppm=10,
    rt_tolerance=0.5,
    ccs_tolerance=2.0,
):
    adjusted_df = adjusted_df.sort_values(by="m/z")
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
    Merges groups into a single feature in the adjusted_df.
    The representative feature is the row with the lowest m/z in the group.
    The intensity values are preserved from the first peak.
    """
    intensity_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]

    for group in groups:
        # Find the rows corresponding to the group
        group_df = adjusted_df[adjusted_df["m/z"].isin(group)]
        # Identify the representative row (lowest m/z)
        representative_row = group_df.loc[group_df["m/z"].idxmin()]

        # Set intensity columns of other rows in the group to match the representative row
        for col in intensity_columns:
            adjusted_df.loc[adjusted_df["m/z"].isin(group), col] = representative_row[
                col
            ]

        # Remove all other rows in the group except the representative row
        adjusted_df = adjusted_df[
            ~(
                adjusted_df["m/z"].isin(group)
                & (adjusted_df["m/z"] != representative_row["m/z"])
            )
        ]

    return adjusted_df
