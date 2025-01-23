import time
import pandas as pd
from scipy.stats import linregress
import matplotlib.pyplot as plt


def mz_repeating_unit_analysis(file_path, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Read the CSV file and extract relevant columns
    data_df = pd.read_csv(file_path)

    # Debug: Print the first few rows of the DataFrame to ensure correct data loading
    print("Preview of loaded data:")
    print(data_df.head())

    # Create a unique composite key using row.ID and m/z
    data_df["unique_key"] = (
        data_df["row.ID"].astype(str) + "_" + data_df["m/z"].astype(str)
    )

    # Convert DataFrame to a dictionary accessible by unique_key
    data_dict = data_df.set_index("unique_key").to_dict("index")

    # Extract required data for processing
    array = data_df["m/z"].tolist()
    row_ids = data_df["row.ID"].tolist()
    ccs_values = data_df["CCS"].tolist()
    scores = data_df["Score"].tolist()

    # Debug: Check if the extracted scores align with the rows
    for i in range(len(array)):
        print(
            f"Row {i + 1}: m/z={array[i]}, Row ID={row_ids[i]}, CCS={ccs_values[i]}, Score={scores[i]}"
        )

    # Get the header value from the 21st column (zero-based index 20)
    try:
        header_value = data_df.columns[20]
    except IndexError:
        raise ValueError(
            "Column U (21st column) does not exist in the dataset headers."
        )

    z = 1
    groups = []
    visited_indices = set()

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
                    current_group.append(
                        (
                            other_mz,
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
        for point in group:
            print(
                f"  m/z: {point[0]}, Row ID: {point[1]}, CCS: {point[2]}, Score: {point[3]}, Header: {point[4]}"
            )

    end_time = time.time()  # End the timer
    execution_time = end_time - start_time
    print(f"Mass repeating unit analysis: {execution_time:.4f} seconds")

    return groups


def CCS_vs_mz_trend_analysis(groups, variation_threshold=0.02):
    homologous_series_groups = []  # Store final groups
    regression_results = {}  # Store regression results
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")

        # Separate A-grade and non-A-grade elements
        a_group = [point for point in group if point[3] in ["A+", "A", "A-"]]
        non_a_group = [point for point in group if point[3] not in ["A+", "A", "A-"]]

        if len(a_group) > 1:  # Ensure there are enough points for regression
            # Extract m/z and CCS values for A-grade points
            a_mz_values = [point[0] for point in a_group]  # m/z is at index 0
            a_ccs_values = [point[2] for point in a_group]  # CCS is at index 2

            # Perform regression and trend analysis
            slope, intercept, r_value, p_value, std_err = linregress(
                a_mz_values, a_ccs_values
            )
            r_squared = r_value**2

            print(
                f"Group {idx + 1} Regression: Slope={slope:.4f}, Intercept={intercept:.4f}, "
                f"R²={r_squared:.4f}, p={p_value:.4f}"
            )

            # Initialize homologous series group with A-grade points
            homologous_group = a_group.copy()

            # Analyze non-A-grade points
            for point in non_a_group:
                mz, ccs = point[0], point[2]  # m/z is at index 0, CCS is at index 2
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

            # Store regression results
            regression_results[f"Group {idx + 1}"] = {
                "slope": slope,
                "intercept": intercept,
                "R_squared": r_squared,
                "p_value": p_value,
                "std_err": std_err,
            }

            # Plot the results
            plt.figure(figsize=(10, 6))
            plt.scatter(a_mz_values, a_ccs_values, color="blue", label="A-grade points")
            plt.plot(
                a_mz_values,
                [slope * mz + intercept for mz in a_mz_values],
                color="blue",
                linestyle="dashed",
                label=f"Trend line (R²={r_squared:.4f}, p={p_value:.4f})",
            )
            for point in non_a_group:
                mz, ccs = point[0], point[2]
                predicted_ccs = slope * mz + intercept
                residual = abs(ccs - predicted_ccs)
                acceptable_variation = variation_threshold * predicted_ccs
                plt.scatter(
                    mz,
                    ccs,
                    color="green" if residual <= acceptable_variation else "red",
                    label="Included"
                    if residual <= acceptable_variation
                    else "Excluded",
                )
            plt.xlabel("m/z")
            plt.ylabel("CCS")
            plt.title(f"Group {idx + 1}: CCS vs m/z")
            plt.legend()
            plt.grid(True)
            plt.show()
        else:
            print(f"Group {idx + 1}: Not enough A-grade points for regression.")
            # Plot the points anyway, if any
            if len(a_group) > 0:
                plt.figure(figsize=(10, 6))
                plt.scatter(
                    [point[0] for point in a_group],
                    [point[2] for point in a_group],
                    color="blue",
                    label="A-grade points",
                )
                plt.xlabel("m/z")
                plt.ylabel("CCS")
                plt.title(f"Group {idx + 1}: CCS vs m/z (Insufficient Points)")
                plt.legend()
                plt.grid(True)
                plt.show()

    return homologous_series_groups, regression_results
