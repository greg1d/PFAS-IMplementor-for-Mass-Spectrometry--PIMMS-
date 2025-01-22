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

            # Start the group with the initial peak
            current_group = set()
            current_group.add(array[i])

            # Check for multiples of M up to 12x
            for multiplier in range(1, 13):
                M_multiple = M * multiplier
                peaks_within_bounds, count = find_peaks_within_bounds(
                    array, z, M_multiple, i, mass_error_ppm
                )
                if count > 0:
                    # Add detected peaks to the current group
                    for peak in peaks_within_bounds:
                        detected_indices.add(array.index(peak))
                        current_group.add(peak)

            # If a valid group is formed, add it to the groups list
            if len(current_group) > 1:
                groups.append(sorted(current_group))

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
