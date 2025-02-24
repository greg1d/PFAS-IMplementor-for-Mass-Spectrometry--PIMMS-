import os
import sys
from scipy.stats import linregress
import pandas as pd
import cmocean
import numpy as np
import plotly.graph_objects as go

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_library_search_modules.library_search_module import (
    get_library_path,
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.CCS_mz_trend_analysis import mz_repeating_unit_analysis

# ✅ Use dynamically selected library path
LIBRARY_PATH = get_library_path()
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
print("[INFO] Library path selected:", LIBRARY_PATH)

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

stacked_df = stack_library_with_adjusted()
mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)

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

    # ✅ Debugging: Print each group separately
    for group_id, df in split_mass_groups.items():
        print(f"\n[DEBUG] Group {group_id} (n={len(df)}):")
        print(df.to_string(index=False))  # Print full DataFrame for clarity

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

    print("\n[INFO] Running RT vs m/z Trend Analysis...")

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
        r_squared = r_value**2  # Compute R²

        print(
            f"[DEBUG] Group {group_id}: slope={slope:.4f}, R²={r_squared:.4f}, p={p_value:.4g}"
        )

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

    print("\n[INFO] RT vs m/z trend analysis completed.")
    print(f"[INFO] Significant RT Groups: {len(significant_RT_group)} rows.")
    print(f"[INFO] Messy RT Groups: {len(messy_RT_group)} rows.")

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

    print("\n[INFO] Refining messy RT groups...")

    # ✅ Group by 'GroupID'
    unique_groups = messy_RT_group["GroupID"].unique()

    significant_RT_groups = []  # ✅ Store newly significant groups
    remaining_messy_groups = []  # ✅ Store groups still not significant

    for group_id in unique_groups:
        subset = messy_RT_group[messy_RT_group["GroupID"] == group_id].copy()

        print(f"\n[DEBUG] Processing Group {group_id} (n={len(subset)})...")
        print(subset.to_string(index=False))  # ✅ Print full group for clarity

        while len(subset) >= 3:
            # ✅ Extract x (m/z) and y (RT)
            x = subset["m/z"].values
            y = subset["RT"].values

            # ✅ Perform linear regression
            slope, intercept, r_value, p_value, _ = linregress(x, y)
            r_squared = r_value**2

            print(
                f"[DEBUG] Group {group_id}: slope={slope:.4f}, R²={r_squared:.4f}, p={p_value:.4g}"
            )

            # ✅ Calculate residuals for each point
            predicted_y = slope * x + intercept
            residuals = y - predicted_y
            abs_residuals = np.abs(residuals)

            # ✅ Print residuals for each point
            subset["Residual"] = residuals
            print(f"\n[DEBUG] Residuals for Group {group_id}:")
            print(subset.to_string(index=False))  # ✅ Print group with residuals

            # ✅ If p < 0.05 and ≥ 3 points, store as significant
            if p_value < 0.05:
                significant_RT_groups.append(subset.drop(columns=["Residual"]))
                print(
                    f"[INFO] Group {group_id}: p={p_value:.4g}, added to significant_RT_group"
                )
                break  # ✅ Stop refining this group

            # ✅ If still p ≥ 0.05, find max residual and remove it
            max_residual_index = np.argmax(abs_residuals)
            max_residual_point = subset.iloc[max_residual_index]

            print(f"[WARNING] Removing outlier: {max_residual_point.to_dict()}")

            # ✅ Remove the outlier
            subset = subset.drop(subset.index[max_residual_index]).reset_index(
                drop=True
            )

        # ✅ If <3 points left, keep in messy group
        if len(subset) < 3:
            remaining_messy_groups.append(subset.drop(columns=["Residual"]))
            print(f"[INFO] Group {group_id}: p still ≥ 0.05, remains in messy_RT_group")

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

    print("\n[INFO] Refinement process complete.")
    print(f"[INFO] Newly significant RT Groups: {len(significant_RT_group)} rows.")
    print(f"[INFO] Remaining messy RT Groups: {len(messy_RT_group)} rows.")

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

    print("\n[INFO] Combining significant RT groups...")

    # ✅ Check if refined_sig_groups has data
    if refined_sig_groups.empty:
        print(
            "[WARNING] No refined significant groups found. Returning original significant_RT_group."
        )
        return significant_RT_group.copy()

    # ✅ Combine both DataFrames
    m_z_RT_groups = pd.concat(
        [significant_RT_group, refined_sig_groups], ignore_index=True
    )

    print(f"[INFO] Final combined m/z_RT_groups contains {len(m_z_RT_groups)} rows.")

    return m_z_RT_groups


def rt_vs_mz_plotly(m_z_RT_groups):
    """
    Generates an interactive Plotly graph for RT vs. m/z analysis with cmocean color mapping
    and marker symbols based on classification type.

    Args:
        m_z_RT_groups (pd.DataFrame): DataFrame containing 'GroupID', 'RT', 'm/z', and 'Classification Type'.

    Returns:
        plotly.graph_objects.Figure: A Plotly figure with trendlines and scatter points.
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
    unique_groups = m_z_RT_groups["GroupID"].unique()
    print(f"[INFO] Plotting {len(unique_groups)} unique GroupIDs.")

    # ✅ Loop through each group
    for idx, (group_id, group_df) in enumerate(m_z_RT_groups.groupby("GroupID")):
        # ✅ Extract x (m/z) and y (RT) for regression
        mz_values = group_df["m/z"].values
        rt_values = group_df["RT"].values

        # ✅ Assign series color using cmocean colormap
        color_idx = idx % NUM_SERIES
        series_color = f"rgb({HOMOLOGOUS_SERIES_COLORS[color_idx][0] * 255}, {HOMOLOGOUS_SERIES_COLORS[color_idx][1] * 255}, {HOMOLOGOUS_SERIES_COLORS[color_idx][2] * 255})"
        legend_group_name = f"group_{group_id}"

        # ✅ Determine marker symbols based on classification type
        symbols = [
            "x" if row["Classification Type"] == "External Library" else "circle"
            for _, row in group_df.iterrows()
        ]

        # ✅ Perform linear regression for trendline
        if len(mz_values) > 2:  # Ensure at least 3 points for regression
            slope, intercept, r_value, p_value, _ = linregress(mz_values, rt_values)

            # ✅ Compute trendline points
            reg_line_x = np.linspace(min(mz_values), max(mz_values), 100)
            reg_line_y = slope * reg_line_x + intercept

            # 🔹 Add trendline
            fig.add_trace(
                go.Scatter(
                    x=reg_line_x,
                    y=reg_line_y,
                    mode="lines",
                    name=f"RT Trend {group_id}",
                    line=dict(color=series_color, dash="dash"),
                    legendgroup=legend_group_name,
                    hoverinfo="skip",
                    visible="legendonly",  # ✅ Hidden until toggled
                    showlegend=False,
                )
            )

        # ✅ Prepare hover metadata
        hover_texts = [
            f"Group: {group_id}<br>m/z: {row['m/z']:.4f}<br>RT: {row['RT']:.2f}<br>Classification: {row['Classification Type']}"
            for _, row in group_df.iterrows()
        ]

        # 🔹 Scatter plot points with hover text and custom markers
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=rt_values,
                mode="markers",
                marker=dict(size=12, color=series_color, symbol=symbols),
                name=f"Group {group_id}",
                legendgroup=legend_group_name,
                showlegend=True,
                hovertext=hover_texts,
                hoverinfo="text",
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


split_mass_groups = split_mass_groups_by_groupid(mass_groups)
sig_groups, messy_groups = rt_vs_mz_trend_analysis(split_mass_groups)
# Print results
refined_sig_groups, remaining_messy_groups = refine_messy_rt_groups(messy_groups)

m_z_RT_groups = combine_significant_groups(sig_groups, refined_sig_groups)
fig = rt_vs_mz_plotly(m_z_RT_groups)
fig.show()
