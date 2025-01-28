import bisect
import pandas as pd


def calculate_mass_error_no_charge(mass, mass_error_ppm=10):
    mass_error = mass * mass_error_ppm * 1e-6
    print(
        f"[DEBUG] Calculating mass error for mass {mass} with ppm {mass_error_ppm}: {mass_error}"
    )
    return mass_error


def find_similar_peaks(array, i, mass_error_ppm=10):
    mass_bound = calculate_mass_error_no_charge(array[i], mass_error_ppm)
    lower_bound = array[i] - mass_bound
    upper_bound = array[i] + mass_bound
    print(
        f"[DEBUG] Finding peaks within bounds for m/z {array[i]}: Lower = {lower_bound}, Upper = {upper_bound}"
    )
    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    peaks_within_bounds = array[j_start:j_end]
    print(f"[DEBUG] Peaks within bounds: {peaks_within_bounds}")
    return peaks_within_bounds, j_end - j_start


def expand_group(
    adjusted_df,
    initial_peak,
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

    print(f"[DEBUG] Starting group expansion with initial peak: {initial_peak}")
    while to_process:
        current_peak = to_process.pop(0)
        current_idx = array.index(current_peak)
        current_rt = rt_array[current_idx]
        current_ccs = ccs_array[current_idx]

        peaks, _ = find_similar_peaks(array, current_idx, mass_error_ppm)
        for peak in peaks:
            idx = array.index(peak)
            if (
                peak not in identified_features
                and abs(rt_array[idx] - current_rt) <= rt_tolerance
                and abs(ccs_array[idx] - current_ccs) / current_ccs * 100
                <= ccs_tolerance
            ):
                print(f"[DEBUG] Adding peak {peak} to group.")
                identified_features.add(peak)
                group.append(peak)
                to_process.append(peak)

    print(f"[DEBUG] Final group for initial peak {initial_peak}: {group}")
    return group


def analyze_adjusted_df(
    adjusted_df,
    mass_error_ppm=10,
    rt_tolerance=0.5,
    ccs_tolerance=2.0,
):
    adjusted_df = adjusted_df.sort_values(by="m/z")
    array = adjusted_df["m/z"].tolist()

    identified_features = set()
    groups = []

    print("[DEBUG] Starting adjusted_df analysis...")
    for i in range(len(array)):
        if array[i] not in identified_features:
            print(f"[DEBUG] Analyzing feature at index {i} with m/z: {array[i]}")
            group = expand_group(
                adjusted_df,
                array[i],
                mass_error_ppm,
                rt_tolerance,
                ccs_tolerance,
            )
            groups.append(group)
            identified_features.update(group)

    print(f"[DEBUG] Total groups identified: {len(groups)}")
    return groups


def merge_groups_into_adjusted_df(adjusted_df, groups):
    """
    Merges groups into a single feature in the adjusted_df.
    The representative feature calculates the average m/z, RT, and CCS.
    For intensity columns, sums the intensities of all rows in the group.
    Single rows with no group are retained as-is.
    """
    intensity_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]
    print("[DEBUG] Starting group merging...")
    rows_to_keep = []

    for group in groups:
        print(f"[DEBUG] Processing group: {group}")
        group_df = adjusted_df[adjusted_df["m/z"].isin(group)]

        # Calculate average m/z, RT, and CCS
        avg_mz = group_df["m/z"].mean()
        avg_rt = group_df["RT"].mean()
        avg_ccs = group_df["CCS"].mean()

        # Create a representative row
        representative_row = group_df.iloc[0].copy()  # Copy metadata from the first row
        representative_row["m/z"] = avg_mz
        representative_row["RT"] = avg_rt
        representative_row["CCS"] = avg_ccs

        # Update intensities by summing across all rows in the group
        for col in intensity_columns:
            representative_row[col] = group_df[col].sum()

        print(
            f"[DEBUG] Representative row for group {group}: "
            f"m/z = {avg_mz}, RT = {avg_rt}, CCS = {avg_ccs}, intensities updated."
        )
        rows_to_keep.append(representative_row)

    # Create a new DataFrame with only the representative rows
    adjusted_df = pd.DataFrame(rows_to_keep)

    print("[DEBUG] Group merging completed.")
    return adjusted_df


def main():
    # Example adjusted_df with rows to process
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.666, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 176.79, 175.79, 175.79, 175.79],
            "m/z": [100, 100.00012, 200, 300, 400],
            "148 B2 16632.d.DeMP": [10, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [20, 20, 10, 10, 10],
        }
    )

    mass_error_ppm = 10
    rt_tolerance = 0.5
    ccs_tolerance = 2.0

    # Identify groups
    groups = analyze_adjusted_df(
        adjusted_df, mass_error_ppm, rt_tolerance, ccs_tolerance
    )

    print(f"Number of groups identified: {len(groups)}")
    for group in groups:
        print(f"Group: {group}")

    # Merge groups into a single feature
    adjusted_df = merge_groups_into_adjusted_df(adjusted_df, groups)

    print("\n[INFO] Updated adjusted_df after merging groups:")
    print(adjusted_df)


if __name__ == "__main__":
    main()
