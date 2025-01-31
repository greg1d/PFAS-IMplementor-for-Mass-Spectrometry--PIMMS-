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
    Identifies features with mass differences corresponding to specific repeating units.
    Compares only to the next peak down (A -> B, B -> C, C -> D).
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

    # Extract required data
    array = adjusted_df["m/z"].tolist()
    row_ids = adjusted_df["ID"].tolist()
    ccs_values = adjusted_df["CCS"].tolist()
    source_files = adjusted_df["Match Source"].tolist()
    names_or_classes = adjusted_df["Match"].tolist()
    scores = adjusted_df["Classification Type"].tolist()

    groups = []

    # Search using multiple repeating units, comparing only the next peak down
    for M in selected_units:
        print(f"\n[INFO] Analyzing with M = {M:.6f}")

        current_group = []  # Store the current group of peaks

        for i in range(len(array) - 1):  # Iterate over all peaks except the last
            mz_value = array[i]
            next_mz_value = array[i + 1]  # Only compare to the next peak

            # Check if the mass difference is a multiple of M
            mass_diff = abs(mz_value - next_mz_value)
            if any(
                abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                for k in range(1, 4)  # Searches for M, 2M, 3M
            ):
                # Append the first peak if it's not in the group yet
                if not current_group:
                    current_group.append(
                        (
                            mz_value,
                            row_ids[i],
                            ccs_values[i],
                            scores[i],
                            source_files[i],
                            names_or_classes[i],
                        )
                    )

                # Append the next peak to the group
                current_group.append(
                    (
                        next_mz_value,
                        row_ids[i + 1],
                        ccs_values[i + 1],
                        scores[i + 1],
                        source_files[i + 1],
                        names_or_classes[i + 1],
                    )
                )

        if len(current_group) > 1:
            groups.append(current_group)

    # Print the matched groups
    for idx, group in enumerate(groups):
        print(f"\n[INFO] Group {idx + 1}:")
        for point in group:
            print(
                f"  m/z: {point[0]:.6f}, ID: {point[1]}, CCS: {point[2]}, "
                f"Classification: {point[3]}, Match Source: {point[4]}, Match: {point[5]}"
            )

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )
    return groups


def CCS_vs_mz_trend_analysis(groups, variation_threshold=0.02):
    homologous_series_groups = []  # Store final groups
    regression_results = {}  # Store regression results

    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")

        # Separate likely and tentative identifications
        likely_group = [point for point in group if point[3] == "likely"]
        tentative_group = [point for point in group if point[3] == "tentative"]

        # Extract m/z, CCS values, source file names, and Match data
        likely_mz_values = [point[0] for point in likely_group]  # m/z
        likely_ccs_values = [point[2] for point in likely_group]  # CCS
        likely_sources = [point[4] for point in likely_group]  # Match Source
        likely_names = [point[5] for point in likely_group]  # Match

        if len(likely_group) < 2:
            print(f"Group {idx + 1}: Not enough points for regression.")
            continue

        # Prepare the base plot
        fig = go.Figure()

        # Add likely-matched points with hover information
        fig.add_trace(
            go.Scatter(
                x=likely_mz_values,
                y=likely_ccs_values,
                mode="markers",
                name="Likely Match",
                marker=dict(color="blue", size=8),
                hovertemplate=(
                    "m/z: %{x}<br>CCS: %{y}<br>Match Source: %{customdata[0]}<br>"
                    "Match: %{customdata[1]}<extra></extra>"
                ),
                customdata=list(zip(likely_sources, likely_names)),  # Custom hover data
            )
        )

        # Perform regression analysis
        slope, intercept, r_value, p_value, std_err = linregress(
            likely_mz_values, likely_ccs_values
        )
        r_squared = r_value**2

        print(
            f"Group {idx + 1} Regression: Slope={slope:.4f}, Intercept={intercept:.4f}, "
            f"R²={r_squared:.4f}, p={p_value:.4f}"
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
                hoverinfo="skip",  # No hover for the trend line
            )
        )

        # Separate included and excluded tentative identifications
        included_points = []
        excluded_points = []
        for point in tentative_group:
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
                        "m/z: %{x}<br>CCS: %{y}<br>Match Source: %{customdata[0]}<br>"
                        "Match: %{customdata[1]}<extra></extra>"
                    ),
                    customdata=list(zip(included_sources, included_names)),
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


def main():
    """Test and debug the analysis with sample adjusted_df before full integration."""
    adjusted_df = pd.DataFrame(
        {
            "Match": [
                "PFEtS",
                "PFPrS",
                "PFBS",
                "PFPeS",
                "PFOS",
            ],
            "Match Source": [
                "PFAS Standards",
                "PFAS Standards",
                "PFAS Standards",
                "PFAS Standards",
                "PFAS Standards",
            ],
            "Classification Type": [
                "likely",
                "likely",
                "likely",
                "likely",
                "likely",
            ],
            "ID": [1, 2, 3, 4, 5],
            "RT": [1.3, 3.2, 5.2, 7.03, 10.12],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [117.4, 125.1, 133.62, 142.2, 168.27],
            "m/z": [198.9494, 248.9462, 298.943, 348.9398, 498.9302],
            "Mass Error (ppm)": [-5, 3, 1, -2, 0],
            "CCS Error (%)": ["N/A", 1.5, -0.5, 2.0, "N/A"],
            "RT Error (%)": ["N/A", 0.5, -1.2, 1.0, "N/A"],
        }
    )

    groups = mz_repeating_unit_analysis(adjusted_df)
    CCS_vs_mz_trend_analysis(groups)


if __name__ == "__main__":
    main()
