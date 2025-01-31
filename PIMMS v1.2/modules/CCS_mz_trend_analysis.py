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
    """Identifies homologous series trends with at least 3 points within 2 repeating units."""
    start_time = time.time()
    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

    groups = []

    print(f"[DEBUG] Total data points: {len(adjusted_df)}")

    for M in selected_units:
        print(f"\n[INFO] Analyzing with M = {M:.6f}")

        for i in range(len(adjusted_df) - 1):  # Iterate over all peaks except the last
            mz_value = adjusted_df.iloc[i]["m/z"]
            current_group = [
                (
                    mz_value,
                    adjusted_df.iloc[i]["ID"],
                    adjusted_df.iloc[i]["CCS"],
                    adjusted_df.iloc[i]["Classification Type"],
                    adjusted_df.iloc[i]["Match Source"],
                    adjusted_df.iloc[i]["Match"],
                )
            ]

            for j in range(i + 1, len(adjusted_df)):  # Only look forward
                next_mz_value = adjusted_df.iloc[j]["m/z"]
                mass_diff = abs(mz_value - next_mz_value)

                # Check if the difference matches M or 2M
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 4)  # Searches for M, 2M
                ):
                    current_group.append(
                        (
                            next_mz_value,
                            adjusted_df.iloc[j]["ID"],
                            adjusted_df.iloc[j]["CCS"],
                            adjusted_df.iloc[j]["Classification Type"],
                            adjusted_df.iloc[j]["Match Source"],
                            adjusted_df.iloc[j]["Match"],
                        )
                    )

            if len(current_group) >= 3:  # Only store groups with 3+ points
                groups.append(current_group)

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )
    # **🔹 Debugging: Print each group in tabular format**
    for idx, group in enumerate(groups):
        print(f"\n[DEBUG] Group {idx + 1} - Homologous Series:")
        df_debug = pd.DataFrame(group)
        print(df_debug.to_string(index=False))  # Print clean table without row index
        print("-" * 80)  # Separator for readability

    return groups


def add_plotly_traces(fig, adjusted_df, groups):
    """Adds homologous series and unrelated points to the plot."""
    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    grouped_mz_values = {point[0] for group in groups for point in group}
    unrelated_df = adjusted_df[~adjusted_df["m/z"].isin(grouped_mz_values)]

    # Plot unrelated points
    for _, row in unrelated_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )
        color = classification_colors.get(classification, "gray")

        sample_info = [
            f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0
        ]
        sample_text = "<br>".join(sample_info) if sample_info else "None"

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=6, color=color),
                name=f"Standalone {classification.capitalize()}",
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                legendgroup="standalone",
                showlegend=False,
                visible="legendonly",  # Initially hidden but can be toggled
            )
        )

    # Plot homologous series trends
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")
        legend_group = f"group_{idx + 1}"

        all_mz_values = [point[0] for point in group]
        all_ccs_values = [point[2] for point in group]

        if len(all_mz_values) < 3:
            print(f"[DEBUG] Group {idx + 1} skipped (less than 3 points)")
            continue

        slope, intercept, r_value, p_value, std_err = linregress(
            all_mz_values, all_ccs_values
        )
        r_squared = r_value**2

        if r_squared <= 0.90:
            print(f"[DEBUG] Group {idx + 1} skipped (R² {r_squared:.4f} too low)")
            continue

        reg_line_x = sorted(all_mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_squared:.4f}")

        # Add trendline
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Trend {idx + 1}",
                line=dict(color="black", dash="dash"),
                legendgroup=legend_group,
                hoverinfo="skip",
                visible=True,
            )
        )

        # Add homologous group points
        for point in group:
            mz, ccs, classification, match_name = point[0], point[2], point[3], point[5]
            color = classification_colors.get(classification, "gray")

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
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    legendgroup=legend_group,
                    showlegend=False,
                )
            )


def create_interactive_plot(adjusted_df, groups):
    """Creates the interactive plot with toggle functionality."""
    fig = go.Figure()
    add_plotly_traces(fig, adjusted_df, groups)

    fig.update_layout(
        title="CCS vs m/z Trends",
        xaxis_title="m/z",
        yaxis_title="CCS",
        template="plotly_white",
        updatemenus=[  # Add dropdown for toggle
            {
                "buttons": [
                    {
                        "label": "Show All Points",
                        "method": "update",
                        "args": [{"visible": [True] * len(fig.data)}],
                    },
                    {
                        "label": "Show Homologous Series Only",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup.startswith("group")
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.9,
                "y": 1.1,
            }
        ],
    )

    fig.show()


def main():
    """Run the analysis and interactive plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)

    print("[DEBUG] First few rows of dataset:")
    print(adjusted_df.head())

    groups = mz_repeating_unit_analysis(adjusted_df)
    create_interactive_plot(adjusted_df, groups)


if __name__ == "__main__":
    main()
