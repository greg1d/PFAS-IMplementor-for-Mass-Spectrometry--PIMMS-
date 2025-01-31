import time
import pandas as pd
from scipy.stats import linregress
import plotly.graph_objects as go

# Define repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "TEST": 100,
}


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=["CF2"]):
    """
    Identifies features with mass differences corresponding to specific repeating units
    without limiting matches to adjacent rows.
    """
    start_time = time.time()

    # Convert repeating unit names to numerical values
    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

    # Ensure required columns exist
    required_columns = [
        "Match",
        "Match Source",
        "Classification Type",
        "ID",
        "RT",
        "DT",
        "CCS",
        "m/z",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (%)",
    ]

    if not all(col in adjusted_df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")

    # Extract data
    array = adjusted_df["m/z"].tolist()
    row_ids = adjusted_df["ID"].tolist()
    ccs_values = adjusted_df["CCS"].tolist()
    source_files = adjusted_df["Match Source"].tolist()
    names_or_classes = adjusted_df["Match"].tolist()
    scores = adjusted_df["Classification Type"].tolist()

    groups = []
    visited_indices = set()

    # Search across all peaks, not just adjacent ones
    for M in selected_units:
        print(f"\n[INFO] Analyzing with M = {M:.6f}")

        for i, mz_value in enumerate(array):
            if i in visited_indices:
                continue  # Skip already visited points

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

            for j in range(len(array)):  # Compare with all peaks
                if j == i or j in visited_indices:
                    continue  # Skip self and already visited ones

                # Check if the mass difference is a multiple of M
                mass_diff = abs(mz_value - array[j])
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 7)  # Searches up to 6 repeating units
                ):
                    visited_indices.add(j)
                    current_group.append(
                        (
                            array[j],
                            row_ids[j],
                            ccs_values[j],
                            scores[j],
                            source_files[j],
                            names_or_classes[j],
                        )
                    )

            if len(current_group) > 1:
                groups.append(current_group)

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )
    return groups


def CCS_vs_mz_trend_analysis(groups, variation_threshold=0.02):
    homologous_series_groups = []  # Store final groups
    regression_results = {}  # Store regression results

    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")

        # Separate likely, tentative, and unmatched identifications
        likely_group = [point for point in group if point[3] == "likely"]
        tentative_group = [point for point in group if point[3] == "tentative"]
        unmatched_group = [point for point in group if point[3] == "unmatched"]

        # Extract m/z, CCS values, source file names, and Match data
        likely_mz_values = [point[0] for point in likely_group]  # m/z
        likely_ccs_values = [point[2] for point in likely_group]  # CCS
        likely_sources = [point[4] for point in likely_group]  # Match Source
        likely_names = [point[5] for point in likely_group]  # Match

        # Regression uses only "likely" points
        if len(likely_mz_values) < 2:
            print(f"Group {idx + 1}: Not enough points for regression.")
            continue

        # Perform regression analysis
        slope, intercept, r_value, p_value, std_err = linregress(
            likely_mz_values, likely_ccs_values
        )
        r_squared = r_value**2

        print(
            f"Group {idx + 1} Regression: Slope={slope:.4f}, Intercept={intercept:.4f}, "
            f"R²={r_squared:.4f}, p={p_value:.4f}"
        )

        # Prepare the base plot
        fig = go.Figure()

        # Add likely-matched points (blue)
        fig.add_trace(
            go.Scatter(
                x=likely_mz_values,
                y=likely_ccs_values,
                mode="markers",
                hovertemplate=(
                    "m/z: %{x}<br>CCS: %{y}<br>Match Source: %{customdata[0]}<br>"
                    "Match: %{customdata[1]}<extra></extra>"
                ),
                name="Likely Match",
                marker=dict(color="blue", size=8),
                customdata=list(zip(likely_sources, likely_names)),
            )
        )

        # Add regression line
        reg_line_x = sorted(likely_mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name="CCS vs m/z trendline",
                line=dict(color="blue", dash="dash"),
                hoverinfo="skip",
            )
        )

        # Separate included and excluded tentative/unmatched points
        included_points = []
        excluded_points = []

        for point in tentative_group + unmatched_group:
            mz, ccs, source, name, category = (
                point[0],
                point[2],
                point[4],
                point[5],
                point[3],
            )
            predicted_ccs = slope * mz + intercept
            residual = abs(ccs - predicted_ccs)
            acceptable_variation = variation_threshold * predicted_ccs

            if residual <= acceptable_variation:
                included_points.append((mz, ccs, source, name, category))
            else:
                excluded_points.append((mz, ccs, source, name))

        # Add included tentative (orange) and unmatched (purple) points
        if included_points:
            included_mz, included_ccs, included_sources, included_names, categories = (
                zip(*included_points)
            )

            fig.add_trace(
                go.Scatter(
                    x=included_mz,
                    y=included_ccs,
                    mode="markers",
                    name="Tentative (Orange) / Unmatched (Purple)",
                    hovertemplate=(
                        "m/z: %{x}<br>CCS: %{y}<br>Match Source: %{customdata[0]}<br>"
                        "Match: %{customdata[1]}<extra></extra>"
                    ),
                    marker=dict(
                        color=[
                            "orange" if cat == "tentative" else "purple"
                            for cat in categories
                        ],
                        size=8,
                    ),
                    customdata=list(zip(included_sources, included_names)),
                )
            )

        # Add excluded points (red X)
        if excluded_points:
            excluded_mz, excluded_ccs, excluded_sources, excluded_names = zip(
                *excluded_points
            )
            fig.add_trace(
                go.Scatter(
                    x=excluded_mz,
                    y=excluded_ccs,
                    mode="markers",
                    name="Excluded from trend line",
                    marker=dict(color="red", size=8, symbol="x"),
                    customdata=list(zip(excluded_sources, excluded_names)),
                )
            )

        fig.update_layout(
            title=f"Group {idx + 1}: CCS vs m/z",
            xaxis_title="m/z",
            yaxis_title="CCS",
            template="plotly_white",
        )

        fig.show()

    return homologous_series_groups, regression_results


def main():
    """Test and debug the analysis with sample adjusted_df before full integration."""

    # Define the file path
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"

    # Define the columns to read
    columns_to_read = [
        "Match",
        "Match Source",
        "Classification Type",
        "ID",
        "RT",
        "DT",
        "CCS",
        "m/z",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (%)",
    ]

    # Read the CSV file
    adjusted_df = pd.read_csv(file_path, usecols=columns_to_read)

    # Display the first few rows
    print(adjusted_df.head())
    groups = mz_repeating_unit_analysis(adjusted_df)
    CCS_vs_mz_trend_analysis(groups)


if __name__ == "__main__":
    main()
