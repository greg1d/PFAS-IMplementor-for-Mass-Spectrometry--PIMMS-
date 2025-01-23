import time

import matplotlib.pyplot as plt
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

    # Get the header from column U (column index 20, zero-based index)
    try:
        header_value = data_df.columns[20]  # Column U corresponds to index 20
    except IndexError:
        raise ValueError(
            "Column U (21st column) does not exist in the dataset headers."
        )
    print(f"Header from column U: {header_value}")

    # Create a list of unique points as (row.ID, m/z, CCS) tuples
    data_points = list(zip(data_df["row.ID"], data_df["m/z"], data_df["CCS"]))
    data_dict = data_df.set_index("row.ID").to_dict(
        "index"
    )  # Data accessible by row.ID

    # Initialize variables
    z = 1
    detected_points = set()  # Track already processed points as (row.ID, m/z, CCS)
    groups = []

    # Find peaks within bounds for each M value
    for M in repeating_units:
        print(f"Analyzing with M = {M}")
        for i, (row_id, mz, ccs) in enumerate(data_points):
            if (row_id, mz, ccs) in detected_points:
                continue  # Skip already processed points

            # Start the group with the initial point
            current_group = [(row_id, mz, ccs, header_value)]

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
    print("\nDetected Groups:")
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}:")
        for row_id, mz, ccs, header_value in group:
            row_data = data_dict[row_id]
            print(
                f"  row.ID={row_id}, m/z={mz}, CCS={ccs}, RT={row_data['Retention Time']}, "
                f"Score={row_data['Score']}, Header Value={header_value}"
            )

    end_time = time.time()  # End the timer
    execution_time = end_time - start_time
    print(f"\nMass repeating unit analysis completed in {execution_time:.4f} seconds")
    return groups


def CCS_vs_mz_trend_analysis(file_path, groups, variation_threshold=0.02):
    import time

    from scipy.stats import pearsonr

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

    # Dictionary to store the regression results
    regression_results = {}

    # List to store homologous series groups
    homologous_series_groups = []

    # Perform trend analysis for A-grade elements and overlay non-A-grade elements
    for idx, group in enumerate(combined_groups):
        # Separate A-grade and non-A-grade elements
        a_group = [mz for mz in group if score_dict.get(mz) in valid_scores]
        non_a_group = [mz for mz in group if score_dict.get(mz) in non_A_scores]

        # Perform Pearson correlation and linear regression for A-grade points
        if len(a_group) > 1:  # Ensure enough points for regression
            a_ccs_values = [ccs_dict[mz] for mz in a_group if mz in ccs_dict]

            # Pearson correlation analysis
            corr_coefficient, p_value = pearsonr(a_group, a_ccs_values)

            # Only proceed if the p-value is significant (p < 0.05)
            if p_value < 0.05:
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
                    "corr_coefficient": corr_coefficient,
                }

                # Initialize the homologous series group with A-grade points
                homologous_group = [
                    {"m/z": mz, "CCS": ccs_dict[mz], "Score": score_dict[mz]}
                    for mz in a_group
                ]

                # Set up the plot
                plt.figure(figsize=(10, 6))
                plt.xlabel("m/z")
                plt.ylabel("CCS")
                plt.title(f"CCS vs m/z for Group {idx + 1} (A-grade only)")
                plt.grid(True)

                # Plot A-grade points and trend line
                plt.scatter(
                    a_group,
                    a_ccs_values,
                    color="blue",
                    label=f"Group {idx + 1} A-grade",
                )
                plt.plot(
                    a_group,
                    [slope * mz + intercept for mz in a_group],
                    color="blue",
                    linestyle="dashed",
                    label=f"Trend (R²={r_squared:.2f}, p={p_value:.4f})",
                )

                # Check alignment of non-A-group points using variation threshold
                if non_a_group:
                    non_a_ccs_values = [
                        ccs_dict[mz] for mz in non_a_group if mz in ccs_dict
                    ]
                    for mz, ccs in zip(non_a_group, non_a_ccs_values):
                        predicted_ccs = slope * mz + intercept
                        residual = abs(ccs - predicted_ccs)
                        acceptable_variation = variation_threshold * predicted_ccs

                        # Print debugging information
                        print(
                            f"Non-A point mz={mz}, observed CCS={ccs}, predicted CCS={predicted_ccs:.4f}, "
                            f"residual={residual:.4f}, acceptable variation={acceptable_variation:.4f}"
                        )

                        # Inclusion/exclusion decision
                        if residual <= acceptable_variation:
                            plt.scatter(
                                mz,
                                ccs,
                                color="green",
                                label=f"Included (Non-A, mz={mz})",
                            )
                            print(f"Point mz={mz} is INCLUDED in the trend.")
                            homologous_group.append(
                                {"m/z": mz, "CCS": ccs, "Score": score_dict[mz]}
                            )
                        else:
                            plt.scatter(
                                mz,
                                ccs,
                                color="red",
                                label=f"Excluded (Non-A, mz={mz})",
                            )
                            print(f"Point mz={mz} is EXCLUDED from the trend.")

                # Add the homologous series group to the list
                homologous_series_groups.append(homologous_group)
                end_time = time.time()  # End the timer
                execution_time = end_time - start_time  # Calculate elapsed time
                print(f"CCS trend analysis: {execution_time:.4f} seconds")
                # Add a legend and show the plot
                plt.legend()
                plt.show()

            else:
                print(f"Group {idx + 1}: No significant trend (p = {p_value:.4f})")

    return homologous_series_groups
