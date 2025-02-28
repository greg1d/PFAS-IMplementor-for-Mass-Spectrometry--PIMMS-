import os
import sys

import cmocean
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import linregress

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_library_search_modules.library_search_module import (
    get_library_path,
    stack_library_with_adjusted,
    mz_repeating_unit_analysis,
)

# ✅ Use dynamically selected library path
LIBRARY_PATH = get_library_path()
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

# ✅ Select a subset of repeating units for analysis
SELECTED_UNITS = ["CF2"]
selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}


NUM_SERIES = 10
HOMOLOGOUS_SERIES_COLORS = cmocean.cm.phase(np.linspace(0, 1, NUM_SERIES))


def split_mass_groups_by_groupid(mass_groups):
    """
    Splits the mass_groups DataFrame into separate DataFrames for each unique GroupID.

    Args:
        mass_groups (pd.DataFrame): DataFrame containing 'GroupID' column.

    Returns:
        dict: A dictionary where keys are GroupIDs and values are the corresponding DataFrames.
    """

    if "GroupID" not in mass_groups.columns:
        raise ValueError("[ERROR] DataFrame must contain 'GroupID' column.")

    # ✅ Group by 'GroupID' and store each subset in a dictionary
    split_mass_groups = {group: df for group, df in mass_groups.groupby("GroupID")}

    return split_mass_groups


def rt_vs_mz_trend_analysis(split_mass_groups):
    """
    Performs trend analysis on RT (Retention Time) vs m/z for each unique GroupID.
    - Categorizes groups into 'significant_RT_group' (p < 0.05) and 'messy_RT_group' (p ≥ 0.05).
    - Returns these two DataFrames separately.

    Args:
        split_mass_groups (dict): Dictionary of DataFrames split by GroupID.

    Returns:
        significant_RT_group (pd.DataFrame): Groups with significant trends (p < 0.05).
        messy_RT_group (pd.DataFrame): Groups with non-significant trends (p ≥ 0.05).
    """

    significant_RT_groups = []  # ✅ Store significant groups
    messy_RT_groups = []  # ✅ Store messy groups

    for group_id, df in split_mass_groups.items():
        print(f"\n[DEBUG] Processing Group {group_id}...")

        if df.shape[0] < 3:
            print(f"[WARNING] Group {group_id} has fewer than 3 points. Skipping.")
            continue

        # ✅ Extract x (m/z) and y (RT)
        x = df["m/z"].values
        y = df["RT"].values

        # ✅ Perform linear regression
        slope, intercept, r_value, p_value, _ = linregress(x, y)

        print(f"[DEBUG] Group {group_id}:  p={p_value:.4g}")

        # ✅ Categorize groups based on p-value
        if p_value < 0.05:
            significant_RT_groups.append(df)  # Store significant group
        else:
            messy_RT_groups.append(df)  # Store messy group

    # ✅ Convert lists to DataFrames
    significant_RT_group = (
        pd.concat(significant_RT_groups, ignore_index=True)
        if significant_RT_groups
        else pd.DataFrame()
    )
    messy_RT_group = (
        pd.concat(messy_RT_groups, ignore_index=True)
        if messy_RT_groups
        else pd.DataFrame()
    )

    return significant_RT_group, messy_RT_group


def refine_messy_rt_groups(messy_RT_group):
    """
    Iteratively removes the point with the highest residual from each messy RT group until:
    - A statistically significant (p < 0.05) group is found with at least 3 points.
    - Or fewer than 3 points remain (group remains messy).

    Args:
        messy_RT_group (pd.DataFrame): Groups where p ≥ 0.05.

    Returns:
        pd.DataFrame: Updated `significant_RT_group` with improved trends.
        pd.DataFrame: Updated `messy_RT_group` (remaining non-significant groups).
    """

    # Check if there is no data or no "GroupID" column; if so, skip processing.
    if messy_RT_group.empty or "GroupID" not in messy_RT_group.columns:
        print("[INFO] No messy RT groups to refine. Skipping refinement.")
        return pd.DataFrame(), pd.DataFrame()

    # ✅ Group by 'GroupID'
    unique_groups = messy_RT_group["GroupID"].unique()

    significant_RT_groups = []  # ✅ Store newly significant groups
    remaining_messy_groups = []  # ✅ Store groups still not significant

    for group_id in unique_groups:
        subset = messy_RT_group[messy_RT_group["GroupID"] == group_id].copy()

        while len(subset) >= 3:
            # ✅ Extract x (m/z) and y (RT)
            x = subset["m/z"].values
            y = subset["RT"].values

            # ✅ Perform linear regression
            slope, intercept, p_value, _ = linregress(x, y)

            # ✅ Calculate residuals for each point
            predicted_y = slope * x + intercept
            residuals = y - predicted_y
            abs_residuals = np.abs(residuals)

            # ✅ Print residuals for each point
            subset["Residual"] = residuals

            # ✅ If p < 0.05 and ≥ 3 points, store as significant
            if p_value < 0.05:
                significant_RT_groups.append(subset.drop(columns=["Residual"]))
                print(
                    f"[INFO] Group {group_id}: p={p_value:.4g}, added to significant_RT_group"
                )
                break  # ✅ Stop refining this group

            # ✅ If still p ≥ 0.05, find max residual and remove it
            max_residual_index = np.argmax(abs_residuals)

            # ✅ Remove the outlier
            subset = subset.drop(subset.index[max_residual_index]).reset_index(
                drop=True
            )

        # ✅ If <3 points left, keep in messy group
        if len(subset) < 3:
            remaining_messy_groups.append(subset.drop(columns=["Residual"]))

    # ✅ Convert lists to DataFrames
    significant_RT_group = (
        pd.concat(significant_RT_groups, ignore_index=True)
        if significant_RT_groups
        else pd.DataFrame()
    )
    messy_RT_group = (
        pd.concat(remaining_messy_groups, ignore_index=True)
        if remaining_messy_groups
        else pd.DataFrame()
    )

    return significant_RT_group, messy_RT_group


def combine_significant_groups(significant_RT_group, refined_sig_groups):
    """
    Combines significant_RT_group with newly refined significant groups (refined_sig_groups).

    Args:
        significant_RT_group (pd.DataFrame): Previously identified significant RT groups.
        refined_sig_groups (pd.DataFrame): Newly refined significant RT groups.

    Returns:
        pd.DataFrame: Final combined DataFrame `m_z_RT_groups`, containing all significant RT groups.
    """

    # ✅ Check if refined_sig_groups has data
    if refined_sig_groups.empty:
        return significant_RT_group.copy()

    # ✅ Combine both DataFrames
    m_z_RT_groups = pd.concat(
        [significant_RT_group, refined_sig_groups], ignore_index=True
    )

    return m_z_RT_groups


def limit_consecutive_external_points(m_z_RT_groups):
    """
    Limits consecutive "External Library" points to a maximum of 3.

    For each group (ordered by m/z), if there are more than 3 consecutive rows with
    'Classification Type' equal to "External Library", only the first 3 will be retained.

    Args:
        m_z_RT_groups (pd.DataFrame): DataFrame containing at least 'GroupID', 'm/z', and 'Classification Type' columns.

    Returns:
        pd.DataFrame: A DataFrame with consecutive "External Library" rows limited to 3.
    """
    # Clean column names
    filtered_groups = []

    # Process each group separately
    for group_id, group in m_z_RT_groups.groupby("GroupID"):
        # Sort each group by m/z
        group_sorted = group.sort_values("m/z").reset_index(drop=True)

        keep_rows = []
        consecutive_external_count = 0

        for idx, row in group_sorted.iterrows():
            # Check classification in a case-insensitive way
            classification = row["Classification Type"].strip().lower()

            if classification == "external library":
                consecutive_external_count += 1
                if consecutive_external_count <= 3:
                    keep_rows.append(row)
                else:
                    # Skip this row, since it's beyond the allowed 3 consecutive external points
                    continue
            else:
                # Reset counter on a non-external row
                consecutive_external_count = 0
                keep_rows.append(row)

        if keep_rows:
            filtered_groups.append(pd.DataFrame(keep_rows))

    # Combine all groups into one DataFrame
    if filtered_groups:
        return pd.concat(filtered_groups, ignore_index=True)
    else:
        return pd.DataFrame(columns=m_z_RT_groups.columns)


def add_back_in_sample_intensities(stacked_df, filtered_m_z_RT_groups):
    """
    Adds sample intensity columns from the stacked DataFrame back into the filtered m/z–RT groups.

    The function:
      - Strips any extra whitespace from column names.
      - Identifies columns in the stacked DataFrame whose header contains ".d" (sample intensity columns).
      - Matches rows between the stacked DataFrame and filtered m/z–RT groups based on the "ID" column.
      - Merges the sample intensity values from the stacked DataFrame into the filtered m/z–RT groups.

    Args:
        stacked_df (pd.DataFrame): DataFrame that includes sample intensity columns (headers containing ".d")
                                   and an "ID" column.
        filtered_m_z_RT_groups (pd.DataFrame): DataFrame of filtered m/z–RT groups with an "ID" column.

    Returns:
        pd.DataFrame: The filtered m/z–RT groups augmented with the sample intensity columns.
    """

    # Clean column names in both DataFrames
    stacked_df.columns = stacked_df.columns.str.strip()
    filtered_m_z_RT_groups.columns = filtered_m_z_RT_groups.columns.str.strip()

    # Identify sample intensity columns from the stacked DataFrame (any column name containing ".d")
    sample_intensity_cols = [col for col in stacked_df.columns if ".d" in col]

    # Check if the "ID" column is present in both DataFrames
    if "ID" not in stacked_df.columns or "ID" not in filtered_m_z_RT_groups.columns:
        print(
            "[WARNING] 'ID' column is missing in one of the DataFrames. Returning filtered_m_z_RT_groups unchanged."
        )
        return filtered_m_z_RT_groups

    # Extract only the "ID" and sample intensity columns from the stacked DataFrame
    intensity_df = stacked_df[["ID"] + sample_intensity_cols]

    # Merge the intensity information into the filtered m/z–RT groups based on the "ID" column.
    # Using a left join ensures that every row in filtered_m_z_RT_groups is kept.
    filtered_m_z_RT_groups = pd.merge(
        filtered_m_z_RT_groups, intensity_df, on="ID", how="left"
    )
    if sample_intensity_cols:
        non_external_mask = (
            filtered_m_z_RT_groups["Classification Type"] != "External Library"
        )
        intensity_mask = (filtered_m_z_RT_groups[sample_intensity_cols] <= 0.001).all(
            axis=1
        )
        # Remove rows that are non-external and have all intensities ≤ 0.001
        final_mask = ~(non_external_mask & intensity_mask)
        filtered_m_z_RT_groups = filtered_m_z_RT_groups.loc[final_mask]

    return filtered_m_z_RT_groups


# ✅ Define color scheme using cmocean
NUM_SERIES = 10  # Adjust based on the number of homologous series
HOMOLOGOUS_SERIES_COLORS = cmocean.cm.phase(np.linspace(0, 1, NUM_SERIES))


def rt_vs_mz_plotly(m_z_RT_groups):
    """
    Generates an interactive Plotly graph for RT vs. m/z analysis with cmocean color mapping.
    - **Trendline (Dashed Line) is hidden by default but toggleable in the legend.**
    - **Points belonging to the trendline remain visible by default but grouped under the trendline.**

    Args:
        m_z_RT_groups (pd.DataFrame): DataFrame containing 'GroupID', 'RT', 'm/z', and 'Classification Type'.

    Returns:
        plotly.graph_objects.Figure: A Plotly figure with trendlines and corresponding points.
    """

    if m_z_RT_groups.empty:
        print("[INFO] No significant RT vs. m/z groups found. Returning blank graph.")
        fig = go.Figure()
        fig.update_layout(
            title="RT vs. m/z (No Significant Groups Found)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>RT (Retention Time)</b>"),
            template="plotly_dark",
        )
        return fig

    fig = go.Figure()

    # ✅ Strip whitespace from column names
    m_z_RT_groups.columns = m_z_RT_groups.columns.str.strip()

    # ✅ Extract unique GroupIDs

    # ✅ **Step 1: Add White "X" and "O" First for Legend**
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=15, color="white", symbol="x"),
            name="<b>External Library Match</b>",  # ✅ Ensure this appears first
            legendgroup="library_match",
            showlegend=True,  # ✅ Always visible
            hoverinfo="skip",
            visible=True,  # ✅ Always visible, not toggled
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=15, color="white", symbol="circle"),
            name="<b>Sample Feature</b>",  # ✅ Ensure this appears second
            legendgroup="sample_feature",
            showlegend=True,  # ✅ Always visible
            hoverinfo="skip",
            visible=True,  # ✅ Always visible, not toggled
        )
    )

    # ✅ **Step 2: Add Trendlines & Corresponding Points**
    for idx, (group_id, group_df) in enumerate(m_z_RT_groups.groupby("GroupID")):
        # ✅ Extract x (m/z) and y (RT) for regression
        mz_values = group_df["m/z"].values
        rt_values = group_df["RT"].values

        # ✅ Assign series color using cmocean colormap
        color_idx = idx % NUM_SERIES
        series_color = f"rgb({HOMOLOGOUS_SERIES_COLORS[color_idx][0] * 255}, {HOMOLOGOUS_SERIES_COLORS[color_idx][1] * 255}, {HOMOLOGOUS_SERIES_COLORS[color_idx][2] * 255})"
        legend_group_name = f"group_{group_id}"

        # ✅ Perform linear regression for trendline
        if len(mz_values) > 2:  # Ensure at least 3 points for regression
            slope, intercept, r_value, p_value, _ = linregress(mz_values, rt_values)

            # ✅ Compute trendline points
            reg_line_x = np.linspace(min(mz_values), max(mz_values), 100)
            reg_line_y = slope * reg_line_x + intercept

            # 🔹 **Dashed Trendline (Hidden by Default, Toggled via Legend)**
            fig.add_trace(
                go.Scatter(
                    x=reg_line_x,
                    y=reg_line_y,
                    mode="lines",
                    name=f"Homologous Series {idx + 1}",
                    line=dict(color=series_color, dash="dash"),
                    legendgroup=legend_group_name,
                    hoverinfo="skip",
                    visible="legendonly",  # ✅ Hidden until toggled
                    showlegend=True,  # ✅ This entry appears in the legend
                )
            )

        # ✅ Prepare hover metadata
        hover_texts = []
        symbols = []
        sample_columns = [col for col in group_df.columns if ".d" in col]
        for _, row in group_df.iterrows():
            match_name = row.get("Match", "No Match")
            classification = row.get("Classification Type", "Unknown")
            RT = row.get("RT", "N/A")  # Safely access RT
            repeating_unit = row.get("Repeating Unit", "N/A")

            # ✅ Assign marker symbol
            marker_symbol = "x" if classification == "External Library" else "circle"
            symbols.append(marker_symbol)
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
                f"RT: {RT}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}"
            )
            # Only add sample details if the classification is not External Library
            if classification != "External Library":
                hover_text += f"<br>Samples:<br>{sample_text}"

            hover_texts.append(hover_text)

        # 🔹 **Scatter plot points with hover text and custom markers**
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=rt_values,
                mode="markers",
                marker=dict(size=15, color=series_color, symbol=symbols),
                name=f"RT Group {idx + 1}",
                legendgroup=legend_group_name,
                hoverinfo="text",
                text=hover_texts,
                visible="legendonly",  # Points are hidden by default
                showlegend=False,  # ✅ Prevent duplicate legend entry
            )
        )

    # ✅ Update Plot Layout
    fig.update_layout(
        title="RT vs. m/z Trend Analysis",
        xaxis=dict(title=r"<b><i>m/z</i></b>"),
        yaxis=dict(title="<b>RT (Retention Time)</b>"),
        template="plotly_dark",
    )

    return fig


def main():
    stacked_df = stack_library_with_adjusted()
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)

    split_mass_groups = split_mass_groups_by_groupid(mass_groups)
    sig_groups, messy_groups = rt_vs_mz_trend_analysis(split_mass_groups)
    refined_sig_groups = refine_messy_rt_groups(messy_groups)

    m_z_RT_groups = combine_significant_groups(sig_groups, refined_sig_groups)

    filtered_m_z_RT_groups = limit_consecutive_external_points(m_z_RT_groups)
    filtered_m_z_RT_groups = add_back_in_sample_intensities(
        stacked_df, filtered_m_z_RT_groups
    )
    fig = rt_vs_mz_plotly(filtered_m_z_RT_groups)
    fig.show()


if __name__ == "__main__":
    main()
