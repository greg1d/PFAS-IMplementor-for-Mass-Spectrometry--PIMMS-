import plotly.graph_objects as go
from scipy.stats import linregress


def make_plotly_graph(adjusted_df, best_subset, post_source_decay, branched_isomers):
    sample_columns = [col for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()

    # ** Remove post-source decay & branched isomer points from general data **
    decay_mz_values = {point[0] for group in post_source_decay for point in group}
    branched_mz_values = {point[0] for group in branched_isomers for point in group}
    excluded_mz_values = decay_mz_values.union(branched_mz_values)
    clean_df = adjusted_df[~adjusted_df["m/z"].isin(excluded_mz_values)]

    # ** Separate DataFrames for Different Groups **
    tentative_df = clean_df[clean_df["Classification Type"] == "tentative"]
    unmatched_df = clean_df[clean_df["Classification Type"] == "unmatched"]
    likely_df = clean_df[clean_df["Classification Type"] == "likely"]

    classification_colors = {
        "likely": "blue",
        "tentative": "orange",
        "unmatched": "purple",
    }

    for _, row in likely_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )

        # ✅ Extract sample intensity info
        sample_info = [
            f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0
        ]
        sample_text = "<br>".join(sample_info) if sample_info else "None"

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=8, color="blue"),
                name="Likely Identified",
                legendgroup="likely_identified",
                showlegend=False,
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                visible=True,  # Initially visible
            )
        )

    # ** Plot Tentative Points **
    for _, row in tentative_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )

        # ✅ Extract sample intensity info
        sample_info = [
            f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0
        ]
        sample_text = "<br>".join(sample_info) if sample_info else "None"

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=8, color="orange"),
                name="Tentative - matched to external library",
                legendgroup="tentative_matched",
                showlegend=False,
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                visible=True,  # Initially visible
            )
        )

    for _, row in unmatched_df.iterrows():
        mz, ccs, classification, match_name = (
            row["m/z"],
            row["CCS"],
            row["Classification Type"],
            row["Match"],
        )

        # ✅ Extract sample intensity info
        sample_info = [
            f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0
        ]
        sample_text = "<br>".join(sample_info) if sample_info else "None"

        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=8, color="purple"),
                name="Tentative - no match to a library",
                legendgroup="tentative_no_match",
                showlegend=False,
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                visible=True,  # Initially visible
            )
        )

    # **🔹 Plot homologous groups with trendlines**
    homologous_series_plotted = False
    homologous_series_groups = []

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
                showlegend=not homologous_series_plotted,
            )
        )
    homologous_series_groups.append(legend_group)
    homologous_series_plotted = True

    for mz, ccs in group:
        row_match = clean_df[clean_df["m/z"] == mz]

        match_name = row_match["Match"].iloc[0] if not row_match.empty else "Unknown"
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
                name=f"Series {idx + 1} Point",
                legendgroup="homologous_series_points",
                showlegend=False,
                hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>"
                f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                visible=True,
            )
        )

    # 🔹 Post-Source Decay Points
    for idx, group in enumerate(post_source_decay):
        for mz, ccs in group:
            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="red"),
                    name=f"Post Source Decay {idx + 1}",
                    legendgroup="post_source_decay",
                    showlegend=True,
                    visible=True,
                )
            )

    # 🔹 Branched Isomer Points
    for idx, group in enumerate(branched_isomers):
        for point in group:
            mz, ccs = point
            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="black"),
                    name=f"Branched Isomer {idx + 1}",
                    legendgroup="branched_isomers",
                    showlegend=True,
                    visible=True,
                )
            )

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
                        "label": "Hide Tentative & No Match Points",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup
                                    not in ["tentative_matched", "tentative_no_match"]
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                    {
                        "label": "Show Tentative & No Match Points",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup
                                    in ["tentative_matched", "tentative_no_match"]
                                    or trace.visible
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                    {
                        "label": "Show Only Likely Identifications",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup == "likely_identified"
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                    {
                        "label": "Show Only Homologous Series",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup
                                    in ["homologous_series", "homologous_series_points"]
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.8,
                "y": 1.15,
            },
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.8,
                "y": 1.08,
                "buttons": [
                    {
                        "label": "Show Post-Source Decay",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup != "post_source_decay"
                                    or trace.visible
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                    {
                        "label": "Hide Post-Source Decay",
                        "method": "update",
                        "args": [
                            {
                                "visible": [
                                    trace.legendgroup != "post_source_decay"
                                    for trace in fig.data
                                ]
                            }
                        ],
                    },
                ],
            },
        ],
    )

    fig.show()
