import time

import pandas as pd
from monoisotopic_peak_puller import find_peaks_within_bounds


def mz_repeating_unit_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract the m/z column
    data_df = pd.read_csv(file_path)
    array = data_df["m/z"].tolist()

    z = 1
    detected_indices = set()
    groups = []

    # Find peaks within bounds for each value in the array for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i in range(len(array)):
            if i in detected_indices:
                continue

            peaks_within_bounds, count = find_peaks_within_bounds(
                array, z, M, i, mass_error_ppm
            )
            if count > 0:
                # Mark all detected peaks to avoid future scans
                for peak in peaks_within_bounds:
                    detected_indices.add(array.index(peak))

                # Add the initial peak to the current group
                current_group = set(peaks_within_bounds)
                current_group.add(array[i])

                # If multiple peaks are found, check for separable by double the M value
                if count >= 1:
                    M_double = M * 2
                    peaks_within_bounds_double, count_double = find_peaks_within_bounds(
                        array, z, M_double, i, mass_error_ppm
                    )
                    if count_double > 0:
                        # Mark all detected peaks for double M value to avoid future scans
                        for peak in peaks_within_bounds_double:
                            detected_indices.add(array.index(peak))

                        # Add the detected peaks to the current group
                        current_group.update(peaks_within_bounds_double)

                # Add the current group to groups
                groups.append(list(current_group))

    # Print the groups and their m/z values
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}: {sorted(group)}")

    end_time = time.time()  # End the timer
    print(f"Execution time: {end_time - start_time} seconds")

    return groups


def CCS_vs_mz_trend_analysis(file_path, groups):
    # Read the CSV file and extract the CCS column
    data_df = pd.read_csv(file_path)
    ccs_dict = data_df.set_index("m/z")["CCS"].to_dict()

    # Print the CCS values for each group
    for idx, group in enumerate(groups):
        ccs_values = [ccs_dict[mz] for mz in group if mz in ccs_dict]
        print(f"Group {idx + 1} CCS values: {ccs_values}")
