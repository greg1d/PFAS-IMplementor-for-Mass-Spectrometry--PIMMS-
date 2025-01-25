import time
import pandas as pd
from scipy.stats import linregress
import plotly.graph_objects as go
import os


def merge_and_extract_data(file_paths, required_columns):
    """
    Merges multiple CSV files and extracts required data while retaining the sample name.

    Parameters:
        file_paths (list): List of CSV file paths to merge.
        required_columns (list): List of required columns to extract.

    Returns:
        pd.DataFrame: A combined DataFrame with relevant data and source file information.
    """
    combined_data = pd.DataFrame()  # Initialize an empty DataFrame
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist. Skipping.")
            continue
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)

            # Check if required columns exist
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                print(
                    f"File {file_path} is missing columns: {missing_columns}. Skipping."
                )
                continue

            # Add the source file name as a column
            df["source_file"] = os.path.basename(file_path)

            # Extract only the required columns + source_file
            df = df[required_columns + ["source_file"]]

            # Append to the combined DataFrame
            combined_data = pd.concat([combined_data, df], ignore_index=True)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    if combined_data.empty:
        raise ValueError(
            "No valid data could be merged. Ensure the files and columns are correct."
        )

    print(
        f"Combined dataset contains {len(combined_data)} rows from {len(file_paths)} files."
    )
    print("combined_data", combined_data)
    return combined_data


def mz_repeating_unit_analysis(data_df, mass_error_ppm=10, repeating_units=[100]):
    start_time = time.time()  # Start the timer

    # Ensure the required columns are present
    required_columns = ["m/z", "Score", "CCS", "row.ID", "source_file", "Name_or_Class"]
    if not all(col in data_df.columns for col in required_columns):
        raise ValueError(
            f"DataFrame is missing one or more required columns: {required_columns}"
        )

    # Extract required data for processing
    array = data_df["m/z"].tolist()
    row_ids = data_df["row.ID"].tolist()
    ccs_values = data_df["CCS"].tolist()
    scores = data_df["Score"].tolist()
    source_files = data_df["source_file"].tolist()
    names_or_classes = data_df["Name_or_Class"].tolist()

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
                (
                    mz_value,
                    row_ids[i],
                    ccs_values[i],
                    scores[i],
                    source_files[i],
                    names_or_classes[i],
                )
            ]
            # Iteratively check all other points
            for j, other_mz in enumerate(array):
                if j == i or j in visited_indices:
                    continue  # Skip the same point or already visited ones

                # Check if the mass difference is a multiple of M
                mass_diff = abs(mz_value - other_mz)
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 6)
                ):
                    visited_indices.add(j)
                    current_group.append(
                        (
                            other_mz,
                            row_ids[j],
                            ccs_values[j],
                            scores[j],
                            source_files[j],
                            names_or_classes[j],
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
                f"  m/z: {point[0]}, Row ID: {point[1]}, CCS: {point[2]}, Score: {point[3]}, Source File: {point[4]}, Name_or_Class: {point[5]}"
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

        # Extract m/z, CCS values, source file names, and Name_or_Class
        a_mz_values = [point[0] for point in a_group]  # m/z
        a_ccs_values = [point[2] for point in a_group]  # CCS
        a_sources = [point[4] for point in a_group]  # Source file
        a_names = [point[5] for point in a_group]  # Name_or_Class

        if len(a_group) < 2:
            print(f"Group {idx + 1}: Not enough points for regression.")
            continue

        # Prepare the base plot
        fig = go.Figure()

        # Add A-grade points with hover information
        fig.add_trace(
            go.Scatter(
                x=a_mz_values,
                y=a_ccs_values,
                mode="markers",
                name="A-grade Library match",
                marker=dict(color="blue", size=8),
                hovertemplate=(
                    "m/z: %{x}<br>CCS: %{y}<br>Source File: %{customdata[0]}<br>"
                    "Name_or_Class: %{customdata[1]}<extra></extra>"
                ),
                customdata=list(zip(a_sources, a_names)),  # Custom hover data
            )
        )

        # Perform regression analysis
        slope, intercept, r_value, p_value, std_err = linregress(
            a_mz_values, a_ccs_values
        )
        r_squared = r_value**2

        print(
            f"Group {idx + 1} Regression: Slope={slope:.4f}, Intercept={intercept:.4f}, "
            f"R²={r_squared:.4f}, p={p_value:.4f}"
        )

        # Add regression line
        reg_line_x = sorted(a_mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name="CCS vs m/z trendline",
                line=dict(color="blue", dash="dash"),
                hoverinfo="skip",  # No hover for the trend line
            )
        )

        # Separate included and excluded non-A-grade points
        included_points = []
        excluded_points = []
        for point in non_a_group:
            mz, ccs, source, name = point[0], point[2], point[4], point[5]
            predicted_ccs = slope * mz + intercept
            residual = abs(ccs - predicted_ccs)
            acceptable_variation = variation_threshold * predicted_ccs
            if residual <= acceptable_variation:
                included_points.append((mz, ccs, source, name))
            else:
                excluded_points.append((mz, ccs, source, name))

        # Add a single trace for all included points
        if included_points:
            included_mz, included_ccs, included_sources, included_names = zip(
                *included_points
            )
            fig.add_trace(
                go.Scatter(
                    x=included_mz,
                    y=included_ccs,
                    mode="markers",
                    name="Included in homologous series trend",
                    marker=dict(color="green", size=8),
                    hovertemplate=(
                        "m/z: %{x}<br>CCS: %{y}<br>Source File: %{customdata[0]}<br>"
                        "Name_or_Class: %{customdata[1]}<extra></extra>"
                    ),
                    customdata=list(zip(included_sources, included_names)),
                )
            )

        # Add a single trace for all excluded points
        if excluded_points:
            excluded_mz, excluded_ccs, excluded_sources, excluded_names = zip(
                *excluded_points
            )
            fig.add_trace(
                go.Scatter(
                    x=excluded_mz,
                    y=excluded_ccs,
                    mode="markers",
                    name="Excluded from homologous series trend",
                    marker=dict(color="red", size=8),
                    hovertemplate=(
                        "m/z: %{x}<br>CCS: %{y}<br>Source File: %{customdata[0]}<br>"
                        "Name_or_Class: %{customdata[1]}<extra></extra>"
                    ),
                    customdata=list(zip(excluded_sources, excluded_names)),
                )
            )

        # Configure plot layout
        fig.update_layout(
            title=f"Group {idx + 1}: CCS vs m/z",
            xaxis_title="m/z",
            yaxis_title="CCS",
            legend=dict(
                title="Legend",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                x=0.5,
                xanchor="center",
            ),
            template="plotly_white",
        )

        # Display the plot
        fig.show()

    return homologous_series_groups, regression_results
