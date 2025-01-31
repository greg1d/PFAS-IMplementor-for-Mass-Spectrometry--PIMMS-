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
    """
    start_time = time.time()

    # Convert repeating unit names to numerical values
    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

    # Extract relevant data
    mz_values = adjusted_df["m/z"].tolist()
    row_ids = adjusted_df["ID"].tolist()
    ccs_values = adjusted_df["CCS"].tolist()
    scores = adjusted_df["Classification Type"].tolist()
    source_files = adjusted_df["Match Source"].tolist()
    names_or_classes = adjusted_df["Match"].tolist()

    groups = []
    visited_indices = set()

    print(f"[DEBUG] Total data points: {len(mz_values)}")

    # Find homologous groups
    for M in selected_units:
        print(f"\n[INFO] Analyzing repeating unit M = {M:.6f}")

        for i, mz_value in enumerate(mz_values):
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

            for j in range(len(mz_values)):
                if j == i or j in visited_indices:
                    continue

                mass_diff = abs(mz_value - mz_values[j])
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 7)
                ):
                    visited_indices.add(j)
                    current_group.append(
                        (
                            mz_values[j],
                            row_ids[j],
                            ccs_values[j],
                            scores[j],
                            source_files[j],
                            names_or_classes[j],
                        )
                    )

            if len(current_group) > 1:
                groups.append(current_group)
                print(f"[DEBUG] Found homologous group of size {len(current_group)}")

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )
    return groups


def CCS_vs_mz_trend_analysis(adjusted_df, groups, variation_threshold=0.02):
    """
    Plots CCS vs. m/z trends, allowing toggling of trendlines and related points.
    """
    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()

    # First, plot **unrelated points** (always visible)
    unrelated_df = adjusted_df[
        ~adjusted_df["m/z"].isin([point[0] for group in groups for point in group])
    ]

    fig.add_trace(
        go.Scatter(
            x=unrelated_df["m/z"],
            y=unrelated_df["CCS"],
            mode="markers",
            marker=dict(size=6, color="gray"),
            name="Unrelated Points",
            hovertemplate="m/z: %{x}<br>CCS: %{y}<br>Unrelated<extra></extra>",
            legendgroup="unrelated",  # Keeps them visible always
            showlegend=True,
        )
    )

    # Now, plot **related groups**
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")
        legend_group = f"group_{idx + 1}"  # Unique ID for toggling

        # Separate by classification
        likely_group = [point for point in group if point[3] == "likely"]
        tentative_group = [point for point in group if point[3] == "tentative"]
        unmatched_group = [point for point in group if point[3] == "unmatched"]

        likely_mz_values = [point[0] for point in likely_group]
        likely_ccs_values = [point[2] for point in likely_group]

        if len(likely_mz_values) < 2:
            continue  # Skip groups with too few points for regression

        # Perform regression
        slope, intercept, r_value, p_value, std_err = linregress(
            likely_mz_values, likely_ccs_values
        )
        reg_line_x = sorted(likely_mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        # Debug print
        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_value**2:.4f}")

        # Add **trendline**, clicking it toggles its points
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Trend {idx + 1}",
                line=dict(color="black", dash="dash"),
                legendgroup=legend_group,
                hoverinfo="skip",
                showlegend=True,
            )
        )

        # Color mapping for points
        classification_colors = {
            "likely": "blue",
            "tentative": "orange",
            "unmatched": "purple",
        }

        # Add **related points**, grouped by legend
        for point in group:
            mz, ccs, classification, match_name = point[0], point[2], point[3], point[5]
            color = classification_colors.get(classification, "gray")

            # Hover text with `.d` sample info
            sample_info = [
                f"{col}: {adjusted_df.loc[adjusted_df['m/z'] == mz, col].values[0]:.2f}"
                for col in sample_columns
                if mz in adjusted_df["m/z"].values
                and adjusted_df.loc[adjusted_df["m/z"] == mz, col].values[0] > 0
            ]
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color=color),
                    hovertemplate=(
                        f"m/z: {mz}<br>CCS: {ccs}<br>Match: {match_name}<br>"
                        f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>"
                    ),
                    legendgroup=legend_group,  # Tied to the trendline
                    showlegend=False,  # Hide legend for individual points
                )
            )

    # Configure layout
    fig.update_layout(
        title="CCS vs m/z Trends",
        xaxis_title="m/z",
        yaxis_title="CCS",
        template="plotly_white",
    )

    fig.show()


def main():
    """Run the analysis and plotting for interactive homologous series visualization."""

    # Define the file path
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"

    # Read the CSV file
    adjusted_df = pd.read_csv(file_path)

    # Debugging: Print first few rows
    print("[DEBUG] First few rows of dataset:")
    print(adjusted_df.head())

    # Run the mass repeating unit analysis
    groups = mz_repeating_unit_analysis(adjusted_df)

    # Run CCS vs m/z trend analysis with interactive filtering
    CCS_vs_mz_trend_analysis(adjusted_df, groups)


if __name__ == "__main__":
    main()
