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

    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

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
                continue

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

    # Identify all points that belong to a homologous group
    grouped_mz_values = {point[0] for group in groups for point in group}

    # Unrelated points: Keep them visible but retain their classification color
    unrelated_df = adjusted_df[~adjusted_df["m/z"].isin(grouped_mz_values)]

    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    for _, row in unrelated_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )
        color = classification_colors.get(classification, "gray")

        # Get `.d` sample intensities
        sample_info = [
            f"{col}: {row[col]:.2f}"
            for col in sample_columns
            if col in row and row[col] > 0
        ]
        sample_text = "<br>".join(sample_info) if sample_info else "None"

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=6, color=color),
                name=f"Standalone {classification.capitalize()}",
                hovertemplate=f"m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                legendgroup="standalone",  # Keep them always visible
                showlegend=False,
            )
        )

    # Now, plot homologous groups
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")
        legend_group = f"group_{idx + 1}"

        # Separate likely, tentative, and unmatched identifications
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

        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_value**2:.4f}")

        # Add trendline (toggles related points)
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

        # Add group points
        for point in group:
            mz, ccs, classification, match_name = point[0], point[2], point[3], point[5]
            color = classification_colors.get(classification, "gray")

            # Get `.d` sample intensities
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
                    hovertemplate=f"m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    legendgroup=legend_group,
                    showlegend=False,  # Hide legend for individual points
                )
            )

    fig.update_layout(
        title="CCS vs m/z Trends",
        xaxis_title="m/z",
        yaxis_title="CCS",
        template="plotly_white",
    )

    fig.show()


def main():
    """Run the analysis and plotting for interactive homologous series visualization."""

    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"

    adjusted_df = pd.read_csv(file_path)

    print("[DEBUG] First few rows of dataset:")
    print(adjusted_df.head())

    groups = mz_repeating_unit_analysis(adjusted_df)

    CCS_vs_mz_trend_analysis(adjusted_df, groups)


if __name__ == "__main__":
    main()
