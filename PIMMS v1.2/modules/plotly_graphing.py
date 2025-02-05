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
                line=dict(color="white", dash="dash"),
                legendgroup="homologous_series",
                hoverinfo="skip",
                visible=True,
                showlegend=False,
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

    for idx, group in enumerate(post_source_decay):
        try:
            if not isinstance(group, list):
                group = [group]

            for point in group:
                mz, ccs = point

                related_series = " & ".join(
                    [str(p[0]) for p in best_subset[idx]]
                    if idx < len(best_subset)
                    else ["Unknown"]
                )

                fig.add_trace(
                    go.Scatter(
                        x=[mz],
                        y=[ccs],
                        mode="markers",
                        marker=dict(size=8, color="red"),
                        name=f"Post Source Decay {idx + 1}",
                        legendgroup="post_source_decay",
                        showlegend=False,
                        hovertemplate=f"Post-source decay of homologous series: {related_series}<br>"
                        f"m/z: {mz}<br>CCS: {ccs}<extra></extra>",
                    )
                )
        except (ValueError, IndexError, TypeError) as e:
            print(f"[ERROR] Invalid post-source decay point format: {group} - {e}")

    for idx, group in enumerate(branched_isomers):
        try:
            if not isinstance(group, list):
                group = [group]

            for point in group:
                mz, ccs = point

                related_series = " & ".join(
                    [str(p[0]) for p in best_subset[idx]]
                    if idx < len(best_subset)
                    else ["Unknown"]
                )

                fig.add_trace(
                    go.Scatter(
                        x=[mz],
                        y=[ccs],
                        mode="markers",
                        marker=dict(size=8, color="#FF69B4"),
                        name=f"Branched Isomer {idx + 1}",
                        legendgroup="branched_isomers",
                        showlegend=False,
                        hovertemplate=f"Branched isomer of homologous series: {related_series}<br>"
                        f"m/z: {mz}<br>CCS: {ccs}<extra></extra>",
                    )
                )
        except (ValueError, IndexError, TypeError) as e:
            print(f"[ERROR] Invalid branched isomer point format: {group} - {e}")

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="markers",
            marker=dict(size=8, color="blue"),
            name="Likely Identified",
            legendgroup="likely_identified",
            showlegend=True,
            visible=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="markers",
            marker=dict(size=8, color="red"),
            name="Post Source Decay",
            legendgroup="post_source_decay",
            showlegend=True,
            visible=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="markers",
            marker=dict(size=8, color="#FF69B4"),
            name="Branched Isomers",
            legendgroup="branched_isomers",
            showlegend=True,
            visible=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="markers",
            marker=dict(size=8, color="orange"),
            name="Tentative - Library Match",
            legendgroup="tentative_matched",
            showlegend=True,
            visible=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="markers",
            marker=dict(size=8, color="purple"),
            name="Unmatched",
            legendgroup="tentative_no_match",
            showlegend=True,
            visible=True,
        )
    )

    # ✅ Add a single legend entry (No extra lines plotted)
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy invisible point to appear in the legend
            y=[None],
            mode="lines",
            line=dict(color="white", dash="dash"),
            name="Homologous Series",
            legendgroup="homologous_series",
            showlegend=True,
            visible=True,
        )
    )

    # ** Update layout: Ensure Post-Source Decay Toggle Works Independently **
    fig.update_layout(
        title="CCS vs m/z Trends",
        xaxis_title="m/z",
        yaxis_title="CCS",
        template="plotly_dark",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
    )

    fig.show()
