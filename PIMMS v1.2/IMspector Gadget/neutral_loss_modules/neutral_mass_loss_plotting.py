import os
import sys

import cmocean
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from neutral_mass_loss_analysis import (
    filter_neutral_loss_groups,
    neutral_loss_analysis,
)

# Define color palette
NUM_SERIES = 10
HOMOLOGOUS_SERIES_COLORS = cmocean.cm.phase(np.linspace(0, 1, NUM_SERIES))

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
import cmocean
import numpy as np
from rt_v_mz_library_search_modules.rt_v_mz_library_searcher import (
    add_back_in_sample_intensities,
)


def dt_vs_mz_plotly(m_z_DT_groups):
    """
    Generates an interactive Plotly graph for DT vs. m/z analysis.

    - **Each homologous series is visually distinct using the cmocean 'phase' colormap.**
    - **No trendline analysis is performed.**
    - **All data points within the same group share the same color.**
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

        # ✅ Prepare hover metadata
        hover_texts = []
        sample_columns = [col for col in group_df.columns if ".d" in col]

        for _, row in group_df.iterrows():
            match_name = row.get("Match", "No Match")
            classification = row.get("Classification Type", "Unknown")
            DT = row.get("DT", "N/A")  # Safely access DT
            repeating_unit = row.get("Repeating Unit", "N/A")

            # ✅ Extract sample intensity details
            sample_info = []
            matched_row = row.to_frame().T
            if not matched_row.empty:
                for col in sample_columns:
                    col_stripped = col.strip()
                    if col_stripped in matched_row.columns:
                        val = matched_row[col_stripped].values[0]
                        try:
                            val = float(val)
                            if pd.notna(val) and val >= 0.001:
                                sample_info.append(f"{col_stripped}: {val:.2f}")
                        except ValueError:
                            print(
                                f"[WARNING] Could not convert value {val} in column {col_stripped} to float."
                            )
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            # --- Construct hover text ---
            hover_text = (
                f"Match: {match_name}<br>"
                f"m/z: {row['m/z']:.4f}<br>"
                f"CCS: {row['CCS']:.2f}<br>"
                f"DT: {DT}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}"
            )
            # Only add sample details if the classification is not External Library
            if classification != "External Library":
                hover_text += f"<br>Samples:<br>{sample_text}"

            hover_texts.append(hover_text)

        # ✅ Scatter plot for the group
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=dt_values,
                mode="markers+text",
                marker=dict(size=15, color=series_color),
                name=f"Group {group_id}",
                legendgroup=f"group_{group_id}",
                showlegend=True,
                text=[
                    f"{row.get('Match', 'No Match')}<br>{row.get('Classification Type', 'Unknown')}"
                    for _, row in group_df.iterrows()
                ],
                textposition="middle left",
                hovertext=hover_texts,
                hoverinfo="text",
                hovertemplate="%{hovertext}<extra></extra>",
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
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}

    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )
    neutral_loss_groups = add_back_in_sample_intensities(
        adjusted_df,
        neutral_loss_groups,
    )
    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss = filter_neutral_loss_groups(
        neutral_loss_groups, dt_threshold=0.1, rt_threshold=1, comparison_type="both"
    )

    fig = dt_vs_mz_plotly(filtered_neutral_loss)
    fig.show()
    print("[INFO] Filtered neutral loss groups:\n", filtered_neutral_loss)


if __name__ == "__main__":
    main()
