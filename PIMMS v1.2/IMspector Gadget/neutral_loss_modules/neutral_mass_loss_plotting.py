import os
import sys

import cmocean
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Define color palette
NUM_SERIES = 10
HOMOLOGOUS_SERIES_COLORS = cmocean.cm.phase(np.linspace(0, 1, NUM_SERIES))

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
import cmocean
import numpy as np
from neutral_mass_loss_analysis import (
    combine_filtered_groups,
    filter_multiple_carboxylic_acids,
    filter_neutral_loss_groups,
    neutral_loss_analysis,
    reanalyze_neutral_loss_and_handle_exclusions,
    refine_messy_groups,
    reorder_group_ids,
)
from rt_v_mz_library_search_modules.rt_v_mz_library_searcher import (
    add_back_in_sample_intensities,
)


def dt_vs_mz_plotly(m_z_DT_groups):
    """
    Generates an interactive Plotly graph for DT vs. m/z analysis.

    - **Each homologous series is visually distinct using the cmocean 'phase' colormap.**
    - **No trendline analysis is performed.**
    - **All data points within the same group share the same color.**
    - **Outliers are plotted as 'X' markers but do NOT appear in the legend.**
    - **Sample intensities are included in hover text.**

    Args:
        m_z_DT_groups (pd.DataFrame): DataFrame containing 'GroupID', 'DT', 'm/z', and 'Classification Type'.

    Returns:
        plotly.graph_objects.Figure: A Plotly figure displaying grouped DT vs. m/z data points.
    """

    if m_z_DT_groups.empty:
        print("[INFO] No significant DT vs. m/z groups found. Returning blank graph.")
        fig = go.Figure()
        fig.update_layout(
            title="DT vs. m/z (No Significant Groups Found)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>Drift Time (DT, ms)</b>"),
            template="plotly_dark",
        )
        return fig

    fig = go.Figure()

    # ✅ Dummy trace for "Outlier" (X) so it appears separately in the legend
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=15, color="white", symbol="x"),
            name="<b>Outlier in RT/DT</b>",
            showlegend=True,
            hoverinfo="skip",
            visible=True,
        )
    )

    # ✅ Strip whitespace from column names
    m_z_DT_groups.columns = m_z_DT_groups.columns.str.strip()

    # ✅ Extract unique GroupIDs and iterate over them
    unique_groups = m_z_DT_groups["GroupID"].unique()
    num_groups = len(unique_groups)

    # ✅ Assign colors from the cmocean "phase" colormap
    colors = [
        f"rgb({int(HOMOLOGOUS_SERIES_COLORS[i % NUM_SERIES][0] * 255)}, "
        f"{int(HOMOLOGOUS_SERIES_COLORS[i % NUM_SERIES][1] * 255)}, "
        f"{int(HOMOLOGOUS_SERIES_COLORS[i % NUM_SERIES][2] * 255)})"
        for i in range(num_groups)
    ]

    for idx, (group_id, group_df) in enumerate(m_z_DT_groups.groupby("GroupID")):
        mz_values = group_df["m/z"].values
        dt_values = group_df["DT"].values
        series_color = colors[idx % NUM_SERIES]  # Assign consistent color per group

        # ✅ Separate outliers from non-outliers
        outlier_mask = group_df["Outlier"] == True
        non_outliers = group_df[~outlier_mask]
        outliers = group_df[outlier_mask]

        # ✅ Prepare hover metadata
        hover_texts = []
        sample_columns = [col for col in group_df.columns if ".d" in col]

        # ✅ Scatter plot for NON-Outliers (circles)
        fig.add_trace(
            go.Scatter(
                x=non_outliers["m/z"],
                y=non_outliers["DT"],
                mode="markers+text",
                marker=dict(size=15, color=series_color, symbol="circle"),
                name=f"Group {group_id}",  # ✅ This appears in the legend
                legendgroup=f"group_{group_id}",
                showlegend=True,
                text=[
                    f"{row.get('Match', 'No Match')}<br>{row.get('Classification Type', 'Unknown')}"
                    for _, row in non_outliers.iterrows()
                ],
                textposition="middle left",
                hoverinfo="text",
                hovertext=[
                    f"Match: {row.get('Match', 'No Match')}<br>"
                    f"m/z: {row['m/z']:.4f}<br>"
                    f"DT: {row['DT']}<br>"
                    f"CCS: {row['CCS']:.2f}<br>"
                    f"RT: {row['RT']:.2f}<br>"
                    f"Adduct: {row['Neutral Loss']}<br>"
                    f"Classification: {row.get('Classification Type', 'Unknown')}"
                    for _, row in non_outliers.iterrows()
                ],
            )
        )

        # ✅ Scatter plot for Outliers (X) (DOES NOT appear in legend)
        if not outliers.empty:
            fig.add_trace(
                go.Scatter(
                    x=outliers["m/z"],
                    y=outliers["DT"],
                    mode="markers+text",
                    marker=dict(size=15, color=series_color, symbol="x"),
                    name=f"Outlier in Group {group_id}",
                    legendgroup=f"group_{group_id}",
                    showlegend=False,  # ✅ Prevents it from appearing in legend
                    text=[
                        f"{row.get('Match', 'No Match')}<br>{row.get('Classification Type', 'Unknown')}"
                        for _, row in outliers.iterrows()
                    ],
                    textposition="middle left",
                    hoverinfo="text",
                    hovertext=[
                        f"Match: {row.get('Match', 'No Match')}<br>"
                        f"m/z: {row['m/z']:.4f}<br>"
                        f"DT: {row['DT']}<br>"
                        f"CCS: {row['CCS']:.2f}<br>"
                        f"RT: {row['RT']:.2f}<br>"
                        f"Adduct: {row['Neutral Loss']}<br>"
                        f"Classification: {row.get('Classification Type', 'Unknown')}"
                        for _, row in outliers.iterrows()
                    ],
                )
            )

    # ✅ Update Plot Layout
    fig.update_layout(
        title="DT vs. m/z Grouped Analysis",
        xaxis=dict(title=r"<b><i>m/z</i></b>"),
        yaxis=dict(title="<b>Drift Time (DT, ms)</b>"),
        template="plotly_dark",
    )

    return fig


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)
    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}
    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )

    # ✅ Define shared parameters
    IM_resolving_power = 60
    IM_tolerance_coefficient = 1
    rt_threshold = 0.5
    comparison_type = "both"
    mass_error_ppm = 10

    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss, messy_df = filter_neutral_loss_groups(
        neutral_loss_groups,
        IM_resolving_power,
        IM_tolerance_coefficient,
        rt_threshold,
        comparison_type,
    )

    final_df, m8_group_df = filter_multiple_carboxylic_acids(
        messy_df,
        mass_error_ppm,
        IM_resolving_power,
        IM_tolerance_coefficient,
        rt_threshold,
    )

    final_combined_df = reanalyze_neutral_loss_and_handle_exclusions(
        final_df, m8_group_df, mass_error_ppm=10, neutral_loss_units=None
    )
    print("final_combined_df inside main", final_combined_df)
    post_extended_refinement = refine_messy_groups(
        final_combined_df,
        rt_threshold,
        comparison_type,
        IM_resolving_power,
        IM_tolerance_coefficient,
    )

    neutral_loss_groups_after_filtering = combine_filtered_groups(
        filtered_neutral_loss, post_extended_refinement
    )
    neutral_loss_groups_after_filtering = add_back_in_sample_intensities(
        adjusted_df,
        neutral_loss_groups_after_filtering,
    )
    neutral_loss_groups_after_filtering = reorder_group_ids(
        neutral_loss_groups_after_filtering
    )
    fig = dt_vs_mz_plotly(neutral_loss_groups_after_filtering)
    fig.show()
    print("[INFO] Filtered neutral loss groups:\n", neutral_loss_groups_after_filtering)


if __name__ == "__main__":
    main()
