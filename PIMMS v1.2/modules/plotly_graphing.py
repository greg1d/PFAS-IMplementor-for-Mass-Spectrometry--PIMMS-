import plotly.graph_objects as go
from scipy.stats import linregress


def make_plotly_graph(adjusted_df, best_subset, post_source_decay, branched_isomers):
    """
    Creates an interactive Plotly graph for visualizing CCS vs. m/z trends.
    - Displays all data points initially.
    - Highlights homologous series trendlines.
    - Differentiates post source decay and branched isomers.
    - Shows sample intensity information in tooltips.
    """

    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()

    # Store all homologous m/z values to exclude from unrelated_df
    homologous_mz_values = {point[0] for group in best_subset for point in group}
    unrelated_df = adjusted_df[~adjusted_df["m/z"].isin(homologous_mz_values)]

    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    # **🔹 Plot all data points first**
    for _, row in adjusted_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],  # ✅ Ensuring match name comes from correct column
        )
        color = classification_colors.get(classification, "gray")

        # **🔹 Extract Sample Information (Intensity Data)**
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
                name="All Data Points",
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                legendgroup="all_points",
                showlegend=False,
                visible=True,
            )
        )

    # **🔹 Plot homologous groups with trendlines**
    homologous_series_plotted = False
    for idx, group in enumerate(best_subset):
        legend_group = f"group_{idx + 1}"

        mz_values = [point[0] for point in group]
        ccs_values = [point[1] for point in group]

        if len(mz_values) < 3:
            continue

        slope, intercept, r_value, _, _ = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        if r_squared <= 0.99:
            continue

        reg_line_x = sorted(mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_squared:.4f}")

        # **Trendline (Show in legend only once)**
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name="Homologous Series" if not homologous_series_plotted else None,
                line=dict(color="black", dash="dash"),
                legendgroup="homologous_series",
                hoverinfo="skip",
                visible=True,
                showlegend=not homologous_series_plotted,  # Show legend only once
            )
        )
        homologous_series_plotted = True

        # **Homologous group points**
        for mz, ccs in group:
            # ✅ Retrieve the correct match name from `adjusted_df`
            row_match = adjusted_df[adjusted_df["m/z"] == mz]

            # ✅ Ensure that match_name and classification exist
            match_name = (
                row_match["Match"].iloc[0] if not row_match.empty else "Unknown"
            )
            classification = (
                row_match["Classification Type"].iloc[0]
                if not row_match.empty
                else "unmatched"
            )

            color = classification_colors.get(classification, "gray")

            # ✅ Extract sample intensity info
            sample_info = [
                f"{col}: {row_match[col].values[0]:.2f}"
                for col in sample_columns
                if not row_match.empty and row_match[col].values[0] > 0
            ]
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color=color),
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                    f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    legendgroup=legend_group,
                    showlegend=False,
                )
            )

    # **🔹 Persistent Legend Elements (Avoid duplicates)**
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

    # ** Dropdown to toggle visibility**
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
