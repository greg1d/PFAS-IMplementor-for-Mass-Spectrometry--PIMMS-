import time

import pandas as pd
from scipy.stats import linregress


import bisect


def mz_repeating_unit_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract relevant columns
    data_df = pd.read_csv(file_path)

    # Get the header from column U (21st column, zero-based index 20)
    try:
        header_value = data_df.columns[20]
    except IndexError:
        raise ValueError(
            "Column U (21st column) does not exist in the dataset headers."
        )

    # Create a unique composite key using row.ID and m/z
    data_df["unique_key"] = (
        data_df["row.ID"].astype(str) + "_" + data_df["m/z"].astype(str)
    )

    # Extract m/z values and initialize variables
    array = sorted(data_df["m/z"].tolist())  # Sort the array for binary search
    row_ids = data_df["row.ID"].tolist()
    ccs_values = data_df["CCS"].tolist()
    scores = data_df["Score"].tolist()
    groups = []
    visited_indices = set()

    # Debug: Print the sorted m/z array
    print(f"Sorted m/z array: {array[:10]}")  # Print the first 10 values for debugging

    # Find peaks within bounds for each value in the array for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i, mz_value in enumerate(array):
            if i in visited_indices:
                continue  # Skip already visited points

            # Start the group with the initial peak
            current_group = [
                (mz_value, row_ids[i], ccs_values[i], scores[i], header_value)
            ]

            # Iteratively check all other points using binary search
            for multiplier in range(1, 13):
                # Calculate the range for the next multiple of M
                target_mass = mz_value + M * multiplier
                lower_bound = target_mass - (mass_error_ppm / 1e6) * target_mass
                upper_bound = target_mass + (mass_error_ppm / 1e6) * target_mass

                # Use binary search to find indices within the range
                j_start = bisect.bisect_left(array, lower_bound, i + 1)
                j_end = bisect.bisect_right(array, upper_bound, i + 1)

                # Add all valid points within the bounds to the group
                for j in range(j_start, j_end):
                    if j not in visited_indices:
                        visited_indices.add(j)
                        current_group.append(
                            (
                                array[j],
                                row_ids[j],
                                ccs_values[j],
                                scores[j],
                                header_value,
                            )
                        )

            # If a valid group is formed, add it to the groups list
            if len(current_group) > 1:
                groups.append(current_group)

    # Print the groups with detailed information
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}:")
        for entry in group:
            print(
                f"  m/z: {entry[0]}, row.ID: {entry[1]}, CCS: {entry[2]}, "
                f"Score: {entry[3]}, Sample ID: {entry[4]}"
            )

    end_time = time.time()  # End the timer
    execution_time = end_time - start_time
    print(f"Mass repeating unit analysis: {execution_time:.4f} seconds")

    return groups


def CCS_vs_mz_trend_analysis(groups, variation_threshold=0.02):
    print("Starting CCS vs m/z trend analysis...")
    print(f"Groups received: {groups}")

    start_time = time.time()  # Start the timer

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

    # Initialize variables
    regression_results = {}  # Store regression results for A-grade points
    homologous_series_groups = []  # Store final groups

    # Process each group
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}: {group}")

        # Separate A-grade and non-A-grade elements
        a_group = [
            point for point in group if point[3] in valid_scores
        ]  # Score is at index 3
        non_a_group = [
            point for point in group if point[3] in non_A_scores
        ]  # Score is at index 3

        print(f"A-grade points: {a_group}")
        print(f"Non-A-grade points: {non_a_group}")

        if len(a_group) > 1:  # Ensure there are enough points for regression
            # Extract m/z and CCS values for A-grade points
            a_mz_values = [point[1] for point in a_group]  # m/z is at index 1
            a_ccs_values = [point[2] for point in a_group]  # CCS is at index 2

            # Perform regression and trend analysis
            slope, intercept, r_value, p_value, std_err = linregress(
                a_mz_values, a_ccs_values
            )
            r_squared = r_value**2

            print(
                f"Group {idx + 1} Regression: Slope={slope}, Intercept={intercept}, R²={r_squared:.4f}, p={p_value:.4f}"
            )

            if p_value < 0.05:  # Check if the trend is statistically significant
                # Store regression results
                regression_results[f"Group {idx + 1}"] = {
                    "slope": slope,
                    "intercept": intercept,
                    "R_squared": r_squared,
                    "p_value": p_value,
                    "std_err": std_err,
                }

                # Initialize homologous series group with A-grade points
                homologous_group = a_group.copy()

                # Analyze non-A-grade points
                for point in non_a_group:
                    mz, ccs = point[1], point[2]
                    predicted_ccs = slope * mz + intercept
                    residual = abs(ccs - predicted_ccs)
                    acceptable_variation = variation_threshold * predicted_ccs

                    print(
                        f"Non-A point: m/z={mz}, observed CCS={ccs}, predicted CCS={predicted_ccs:.4f}, "
                        f"residual={residual:.4f}, acceptable variation={acceptable_variation:.4f}"
                    )

                    # Include or exclude based on residual
                    if residual <= acceptable_variation:
                        print(f"Point {point} is INCLUDED in the trend.")
                        homologous_group.append(point)
                    else:
                        print(f"Point {point} is EXCLUDED from the trend.")

                # Add the homologous series group to the final list
                homologous_series_groups.append(homologous_group)

    end_time = time.time()  # End the timer
    execution_time = end_time - start_time
    print(f"\nCCS trend analysis completed in {execution_time:.4f} seconds")

    return homologous_series_groups
