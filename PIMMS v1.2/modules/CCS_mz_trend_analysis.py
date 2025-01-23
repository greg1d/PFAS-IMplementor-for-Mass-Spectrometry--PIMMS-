import time
import pandas as pd
from scipy.stats import linregress
import matplotlib.pyplot as plt


def mz_repeating_unit_analysis(file_paths, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer
    # Ensure file_paths is a list
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    # Load and combine multiple CSVs into a single DataFrame
    print("Loading and combining data from multiple CSVs...")
    data_frames = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df["source_file"] = file_path  # Add a column to track the source file
        data_frames.append(df)

    data_df = pd.concat(data_frames, ignore_index=True)
    print(f"Combined dataset contains {len(data_df)} rows.")

    # Extract required data for processing
    array = data_df["m/z"].tolist()
    row_ids = data_df["row.ID"].tolist()
    ccs_values = data_df["CCS"].tolist()
    scores = data_df["Score"].tolist()

    # Get the header value from the 21st column (zero-based index 20)
    try:
        header_value = data_df.columns[20]
    except IndexError:
        raise ValueError(
            "Column U (21st column) does not exist in the dataset headers."
        )

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
        non_a_group = [point for point in group if point[3] not in ["A+", "A-", "A"]]

        # Extract m/z and CCS values
        a_mz_values = [point[0] for point in a_group]  # m/z
        a_ccs_values = [point[2] for point in a_group]  # CCS

        # Plot data for the current group
        plt.figure(figsize=(10, 6))
        plt.scatter(
            a_mz_values, a_ccs_values, color="blue", label="A-grade points", zorder=5
        )

        # Perform regression analysis if there are enough points
        if len(a_group) > 1:
            slope, intercept, r_value, p_value, std_err = linregress(
                a_mz_values, a_ccs_values
            )
            r_squared = r_value**2

            print(
                f"Group {idx + 1} Regression: Slope={slope:.4f}, Intercept={intercept:.4f}, "
                f"R²={r_squared:.4f}, p={p_value:.4f}"
            )

            # Add regression results to the dictionary
            regression_results[f"Group {idx + 1}"] = {
                "slope": slope,
                "intercept": intercept,
                "R_squared": r_squared,
                "p_value": p_value,
                "std_err": std_err,
            }

            # Plot regression line
            plt.plot(
                a_mz_values,
                [slope * mz + intercept for mz in a_mz_values],
                color="blue",
                linestyle="dashed",
                label=f"Trend (R²={r_squared:.4f})",
                zorder=4,
            )

            # Analyze and plot non-A-grade points
            for point in non_a_group:
                mz, ccs = point[0], point[2]  # m/z, CCS
                predicted_ccs = slope * mz + intercept
                residual = abs(ccs - predicted_ccs)
                acceptable_variation = variation_threshold * predicted_ccs

                if residual <= acceptable_variation:
                    plt.scatter(
                        mz, ccs, color="green", label="Included Non-A", zorder=3
                    )
                else:
                    plt.scatter(mz, ccs, color="red", label="Excluded Non-A", zorder=3)
        else:
            print(f"Group {idx + 1}: Not enough A-grade points for regression.")

        # Finalize plot for the group
        plt.xlabel("m/z")
        plt.ylabel("CCS")
        plt.title(f"Group {idx + 1}: CCS vs m/z")
        plt.legend(loc="upper left")
        plt.grid(True)
        plt.show()

    return homologous_series_groups, regression_results
