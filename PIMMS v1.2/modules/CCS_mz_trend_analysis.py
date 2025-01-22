import time

import matplotlib.pyplot as plt
import pandas as pd
from monoisotopic_peak_puller import find_peaks_within_bounds
from scipy.stats import linregress


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
    execution_time = end_time - start_time
    print(f"Mass repeating unit analysis: {execution_time:.4f} seconds")

    return groups


def CCS_vs_mz_trend_analysis(file_path, groups, residual_threshold=2):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract the CCS and Score columns
    data_df = pd.read_csv(file_path)
    ccs_dict = data_df.set_index("m/z")["CCS"].to_dict()
    score_dict = data_df.set_index("m/z")["Score"].to_dict()

    # Define valid scores for A-grade and non-A-grade groups
    valid_scores = ["A+", "A", "A-"]
    non_A_scores = [
        "B+",
        "B",
        "B-",
        "C+",
        "C",
        "C-",
        "D+",
        "D",
        "D-",
        "E",
    ]

    # Filter the groups to include both A-grade and non-A-grade elements
    combined_groups = []  # Groups containing both A-grade and non-A-grade elements
    for group in groups:
        filtered_group = [mz for mz in group if mz in score_dict]
        if filtered_group:
            combined_groups.append(filtered_group)

    # Set up the plot
    plt.figure(figsize=(10, 6))
    plt.xlabel("m/z")
    plt.ylabel("CCS")
    plt.title("CCS vs m/z")
    plt.grid(True)

    # Perform trend analysis for A-grade elements and overlay non-A-grade elements
    regression_results = {}
    for idx, group in enumerate(combined_groups):
        # Separate A-grade and non-A-grade elements
        a_group = [mz for mz in group if score_dict.get(mz) in valid_scores]
        non_a_group = [mz for mz in group if score_dict.get(mz) in non_A_scores]

        # Plot trend line using A-grade group only
        if len(a_group) > 1:  # Ensure enough points for regression
            a_ccs_values = [ccs_dict[mz] for mz in a_group if mz in ccs_dict]
            slope, intercept, r_value, p_value, std_err = linregress(
                a_group, a_ccs_values
            )
            r_squared = r_value**2

            # Store regression results
            regression_results[f"Group {idx + 1}"] = {
                "slope": slope,
                "intercept": intercept,
                "R_squared": r_squared,
                "p_value": p_value,
                "std_err": std_err,
            }

            # Plot A-grade points and trend line
            plt.scatter(
                a_group, a_ccs_values, color="blue", label=f"Group {idx + 1} A-grade"
            )
            plt.plot(
                a_group,
                [slope * mz + intercept for mz in a_group],
                color="blue",
                linestyle="dashed",
                label=f"Group {idx + 1} Trend (R²={r_squared:.2f})",
            )

        # Overlay non-A-grade points on the same plot
        if non_a_group:
            non_a_ccs_values = [ccs_dict[mz] for mz in non_a_group if mz in ccs_dict]
            plt.scatter(
                non_a_group,
                non_a_ccs_values,
                color="red",
                marker="x",
                label=f"Group {idx + 1} Non-A-grade",
            )
    end_time = time.time()  # End the timer
    execution_time = end_time - start_time  # Calculate elapsed time
    print(f"CCS trend analysis: {execution_time:.4f} seconds")
    # Add a legend and show the plot
    plt.legend()
    plt.show()

    return regression_results
