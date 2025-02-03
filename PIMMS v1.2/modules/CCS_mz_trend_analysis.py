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


# Define repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "TEST": 100,
}


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=["CF2"]):
    """Identifies homologous series trends with at least 3 points using an expanding search approach."""

    start_time = time.time()
    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

    # **Sort data by m/z to ensure proper trend building**
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)

    used_indices = set()  # Track indices that are already included in a group
    groups = []

    print(f"[DEBUG] Total data points: {len(adjusted_df)}")

    for M in selected_units:
        print(f"\n[INFO] Analyzing with M = {M:.6f}")

        for i in range(len(adjusted_df)):  # Iterate over all peaks
            if i in used_indices:
                continue  # Skip if already assigned to a group

            mz_value = adjusted_df.iloc[i]["m/z"]
            current_group = [
                {
                    "m/z": mz_value,
                    "ID": adjusted_df.iloc[i]["ID"],
                    "CCS": adjusted_df.iloc[i]["CCS"],
                    "Classification Type": adjusted_df.iloc[i]["Classification Type"],
                    "Match Source": adjusted_df.iloc[i]["Match Source"],
                    "Match": adjusted_df.iloc[i]["Match"],
                }
            ]
            used_indices.add(i)

            # **Dynamic Expansion Search**
            search_queue = [i]  # Queue to hold indices to check forward

            while search_queue:
                current_idx = search_queue.pop(0)  # Pop the next index to search from
                current_mz = adjusted_df.iloc[current_idx]["m/z"]

                for j in range(current_idx + 1, len(adjusted_df)):  # Look forward
                    if j in used_indices:
                        continue

                    next_mz_value = adjusted_df.iloc[j]["m/z"]
                    mass_diff = abs(current_mz - next_mz_value)

                    # **Check if the difference matches M or 2M from the latest point**
                    if any(
                        abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * current_mz
                        for k in range(1, 3)  # Searches for M, 2M
                    ):
                        current_group.append(
                            {
                                "m/z": next_mz_value,
                                "ID": adjusted_df.iloc[j]["ID"],
                                "CCS": adjusted_df.iloc[j]["CCS"],
                                "Classification Type": adjusted_df.iloc[j][
                                    "Classification Type"
                                ],
                                "Match Source": adjusted_df.iloc[j]["Match Source"],
                                "Match": adjusted_df.iloc[j]["Match"],
                            }
                        )
                        used_indices.add(j)  # Mark as used
                        search_queue.append(
                            j
                        )  # Add this index to keep searching forward

            if len(current_group) >= 3:  # Only store groups with 3+ points
                groups.append(current_group)

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )

    # **Debugging: Print each group in tabular format**
    for idx, group in enumerate(groups):
        print(f"\n[DEBUG] Group {idx + 1} - Homologous Series:")
        df_debug = pd.DataFrame(group)
        print(df_debug.to_string(index=False))  # Print clean table without row index
        print("-" * 80)  # Separator for readability

    return groups


def CCS_vs_mz_trend_analysis(adjusted_df, groups, variation_threshold=0.02):
    """
    Plots CCS vs. m/z trends with interactive group toggling and sample source tracking.
    """

    # Identify all sample columns (columns containing '.d')
    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()

    grouped_mz_values = {point["m/z"] for group in groups for point in group}

    # Unrelated (non-homologous) points
    unrelated_df = adjusted_df[~adjusted_df["m/z"].isin(grouped_mz_values)]

    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    # 🔹 **Plot all unrelated points (Can be toggled)**
    for _, row in unrelated_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )
        color = classification_colors.get(classification, "gray")

        # Extract sample intensities
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
                name="Unrelated Points",
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                legendgroup="unrelated",
                showlegend=True,
                visible=True,  # Initially visible
            )
        )

    # 🔹 **Plot homologous groups with trendlines**
    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")
        legend_group = f"group_{idx + 1}"

        mz_values = [point["m/z"] for point in group]
        ccs_values = [point["CCS"] for point in group]

        if len(mz_values) < 3:
            print(f"[DEBUG] Group {idx + 1} skipped (less than 3 points)")
            continue

        slope, intercept, r_value, p_value, std_err = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        if r_squared <= 0.90:
            print(f"[DEBUG] Group {idx + 1} skipped (R² {r_squared:.4f} too low)")
            continue

        reg_line_x = sorted(mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_squared:.4f}")

        # **Trendline (Only visible when homologous series is shown)**
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Trend {idx + 1}",
                line=dict(color="black", dash="dash"),
                legendgroup=legend_group,
                hoverinfo="skip",
                visible="legendonly",  # Initially hidden, toggled ON with homologous series
            )
        )

        # **Homologous group points**
        for point in group:
            mz, ccs, classification, match_name = (
                point["m/z"],
                point["CCS"],
                point["Classification Type"],
                point["Match"],
            )
            color = classification_colors.get(classification, "gray")

            # Extract sample sources and intensities
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
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<br>Sample Sources:<br>{sample_text}<extra></extra>",
                    legendgroup=legend_group,
                    showlegend=False,
                    visible="legendonly",  # Initially hidden, toggled ON with homologous series
                )
            )

    # **🔹 Toggle Button for "Show All Points" vs. "Only Homologous Series"**
    fig.update_layout(
        title="CCS vs m/z Trends",
        xaxis_title="m/z",
        yaxis_title="CCS",
        template="plotly_white",
        updatemenus=[
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
    CCS_vs_mz_trend_analysis(adjusted_df, groups)


if __name__ == "__main__":
    main()
