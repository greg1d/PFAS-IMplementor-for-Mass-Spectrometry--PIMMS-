import time

import pandas as pd
from monoisotopic_peak_puller import find_peaks_within_bounds
from scipy.stats import linregress


def mz_repeating_unit_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract required columns
    print("Loading data...")
    data_df = pd.read_csv(file_path)
    print("Data loaded successfully. Preview of the dataset:")
    print(data_df.head())

    # Get the header from column U (21st column, zero-based index 20)
    try:
        header_value = data_df.columns[20]
    except IndexError:
        raise ValueError(
            "Column U (21st column) does not exist in the dataset headers."
        )
    print(f"Header from column U: {header_value}")

    # Create a list of unique points as (row.ID, m/z, CCS, Score) tuples
    data_points = list(
        zip(
            data_df["row.ID"],
            data_df["m/z"],
            data_df["CCS"],
            data_df["Score"],
        )
    )
    data_dict = data_df.set_index("row.ID").to_dict(
        "index"
    )  # Data accessible by row.ID

    # Initialize variables
    z = 1
    detected_points = (
        set()
    )  # Track already processed points as (row.ID, m/z, CCS, Score)
    groups = []

    # Find peaks within bounds for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i, (row_id, mz, ccs, score) in enumerate(data_points):
            if (row_id, mz, ccs, score) in detected_points:
                continue  # Skip already processed points

            # Start the group with the initial point
            current_group = [(row_id, mz, ccs, score, header_value)]

            # Check for multiples of M up to 12x
            for multiplier in range(1, 13):
                M_multiple = M * multiplier
                peaks_within_bounds, count = find_peaks_within_bounds(
                    [point[1] for point in data_points],  # Extract m/z values
                    z,
                    M_multiple,
                    i,
                    mass_error_ppm,
                )
                if count > 0:
                    # Add detected peaks to the current group
                    for peak in peaks_within_bounds:
                        for point in data_points:
                            if point[1] == peak and point not in detected_points:
                                detected_points.add(point)
                                current_group.append((*point, header_value))

            # If a valid group is formed, add it to the groups list
            if len(current_group) > 1:
                groups.append(current_group)

    # Print the groups with detailed information

    end_time = time.time()  # End the timer
    execution_time = end_time - start_time
    print(f"\nMass repeating unit analysis completed in {execution_time:.4f} seconds")
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
