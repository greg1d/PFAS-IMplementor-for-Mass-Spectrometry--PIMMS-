import pandas as pd
from neutral_mass_loss_analysis import (
    neutral_loss_analysis,
    filter_neutral_loss_groups,
)
import plotly.graph_objects as go
import numpy as np


def dt_vs_mz_plotly(m_z_DT_groups):
    """
    Generates an interactive Plotly graph for DT vs. m/z analysis.

    - **Each homologous series is visually distinct using color.**
    - **No trendline analysis is performed.**
    - **All data points within the same group share the same color.**

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

    # Generate a unique color for each group
    colors = [
        f"rgb({np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {np.random.randint(0, 255)})"
        for _ in range(num_groups)
    ]

    for idx, (group_id, group_df) in enumerate(m_z_DT_groups.groupby("GroupID")):
        mz_values = group_df["m/z"].values
        dt_values = group_df["DT"].values
        series_color = colors[idx % num_groups]  # Assign consistent color per group

        # ✅ Prepare hover metadata
        hover_texts = []
        symbols = []
        for _, row in group_df.iterrows():
            match_name = row.get("Match", "No Match")
            classification = row.get("Classification Type", "Unknown")
            DT = row.get("DT", "N/A")  # Safely access DT
            repeating_unit = row.get("Repeating Unit", "N/A")

            # ✅ Assign marker symbol
            marker_symbol = "x" if classification == "External Library" else "circle"
            symbols.append(marker_symbol)

            # --- Construct hover text ---
            hover_text = (
                f"Match: {match_name}<br>"
                f"m/z: {row['m/z']:.4f}<br>"
                f"CCS: {row['CCS']:.2f}<br>"
                f"DT: {DT}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}"
            )

            hover_texts.append(hover_text)

        # ✅ Scatter plot for the group
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=dt_values,
                mode="markers+text",
                marker=dict(size=15, color=series_color, symbol=symbols),
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

    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss = filter_neutral_loss_groups(
        neutral_loss_groups, dt_threshold=0.1, rt_threshold=1, comparison_type="both"
    )
    fig = dt_vs_mz_plotly(filtered_neutral_loss)
    fig.show()
    print("[INFO] Filtered neutral loss groups:\n", filtered_neutral_loss)


if __name__ == "__main__":
    main()
