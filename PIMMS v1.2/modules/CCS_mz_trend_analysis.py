import time

import pandas as pd
from scipy.stats import linregress


def mz_repeating_unit_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    import time

    start_time = time.time()  # Start the timer

    # Read the CSV file and extract relevant columns
    data_df = pd.read_csv(file_path)

    # Create a unique composite key using row.ID and m/z
    data_df["unique_key"] = (
        data_df["row.ID"].astype(str) + "_" + data_df["m/z"].astype(str)
    )

    # Convert DataFrame to a dictionary accessible by unique_key
    data_dict = data_df.set_index("unique_key").to_dict("index")

    # Extract m/z values and initialize variables
    array = data_df["m/z"].tolist()
    row_ids = data_df["row.ID"].tolist()
    z = 1
    groups = []
    visited_indices = set()

    # Debug: Print the data dictionary keys
    print(
        f"Unique keys in data_dict: {list(data_dict.keys())[:5]}"
    )  # Print first 5 keys

    # Find peaks within bounds for each value in the array for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i, mz_value in enumerate(array):
            if i in visited_indices:
                continue  # Skip already visited points

            # Start the group with the initial peak
            current_group = [(mz_value, row_ids[i])]

            # Iteratively check all other points
            for j, other_mz in enumerate(array):
                if j == i or j in visited_indices:
                    continue  # Skip the same point or already visited ones

                # Check if the mass difference is a multiple of M
                mass_diff = abs(mz_value - other_mz)
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 13)
                ):
                    visited_indices.add(j)
                    current_group.append((other_mz, row_ids[j]))

            # If a valid group is formed, add it to the groups list
            if len(current_group) > 1:
                groups.append(current_group)

    # Print the groups with m/z and row.ID values
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}: {group}")

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
