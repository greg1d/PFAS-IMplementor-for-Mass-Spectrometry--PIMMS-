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
    Plots CCS vs. m/z trends with interactive group toggling.
    """

    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()

    grouped_mz_values = {point["m/z"] for group in groups for point in group}
    unrelated_df = adjusted_df[~adjusted_df["m/z"].isin(grouped_mz_values)]

    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    # **🔹 Plot all points first (default ON)**
    for _, row in adjusted_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )
        color = classification_colors.get(classification, "gray")

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=6, color=color),
                name="All Data Points",
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<extra></extra>",
                legendgroup="all_points",
                showlegend=False,
                visible=True,
            )
        )

    # **🔹 Plot homologous series with trendlines**
    for idx, group in enumerate(groups):
        legend_group = f"group_{idx + 1}"

        mz_values = [point["m/z"] for point in group]
        ccs_values = [point["CCS"] for point in group]

        if len(mz_values) < 3:
            continue

        slope, intercept, r_value, p_value, std_err = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        if r_squared <= 0.90:
            continue

        reg_line_x = sorted(mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        # **Trendline (Always in legend)**
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name="Homologous Series",
                line=dict(color="black", dash="dash"),
                legendgroup="homologous_series",
                hoverinfo="skip",
                visible=True,
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

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color=color),
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<extra></extra>",
                    legendgroup=legend_group,
                    showlegend=False,
                    visible=True,
                )
            )

    # **🔹 Persistent Legend Elements**
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="black", dash="dash"),
            name="Homologous Series",
            legendgroup="homologous_series",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(color="orange", size=8),
            name="Tentative - matched to external library",
            legendgroup="tentative_matched",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(color="purple", size=8),
            name="Tentative - no match to a library",
            legendgroup="tentative_no_match",
            showlegend=True,
        )
    )

    # **🔹 Dropdown to toggle visibility**
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
                        "label": "Show Only Homologous Series",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup.startswith("homologous_series")
                                    or trace.legendgroup.startswith("group")
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
