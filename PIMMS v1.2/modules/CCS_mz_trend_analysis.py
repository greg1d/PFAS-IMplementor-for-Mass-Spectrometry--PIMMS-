import time
import pandas as pd
from monoisotopic_peak_puller import find_peaks_within_bounds


def ccs_v_mz_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract the m/z column
    data_df = pd.read_csv(file_path)
    array = data_df["m/z"].tolist()

    z = 1

    # Find peaks within bounds for each value in the array for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i in range(len(array)):
            peaks_within_bounds, count = find_peaks_within_bounds(
                array, z, M, i, mass_error_ppm
            )
            print(f"Peaks within bounds for index {i}: {peaks_within_bounds}")
            print(f"Count: {count}")

            # If multiple peaks are found, check for separable by double the M value
            if count >= 1:
                M_double = M * 2
                peaks_within_bounds_double, count_double = find_peaks_within_bounds(
                    array, z, M_double, i, mass_error_ppm
                )
                print(
                    f"Peaks within bounds for index {i} with M = {M_double}: {peaks_within_bounds_double}"
                )
                print(f"Count: {count_double}")

    end_time = time.time()  # End the timer
    print(f"Execution time: {end_time - start_time} seconds")
