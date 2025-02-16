import os
import sys

import numpy as np
import plotly.graph_objects as go
from scipy import stats

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
import pandas as pd
from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)

# Define file paths
FILE_PATH = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
LIBRARY_PATH = "PIMMS v1.2/import folder/Library test file 1.csv"

# ✅ Extract the filename without extension for "Match Source"
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

# ✅ Define all available repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

# ✅ Select a subset of repeating units for analysis
SELECTED_UNITS = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]
selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}


# ✅ Define legend color mapping
LEGEND_ITEMS = {
    "likely": {"color": "blue", "legendgroup": "likely_identified"},
    "Tentative - Library Match": {
        "color": "orange",
        "legendgroup": "tentative_matched",
    },
    "Unmatched": {"color": "purple", "legendgroup": "tentative_no_match"},
    "N/A": {"color": "white", "legendgroup": "NA"},  # ✅ Make N/A white
}


def make_plotly_graph(adjusted_df, filtered_IM_group, library_match_source):
    fig = go.Figure()

    # ✅ Dummy trace for "External Library Match" (X)
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=10, color="white", symbol="x"),
            name="External Library Match",
            legendgroup="library_match",
            showlegend=True,  # ✅ Always visible
            hoverinfo="skip",
            visible=True,  # ✅ Always visible, not toggled
        )
    )

    # ✅ Dummy trace for "Sample Feature" (O)
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=10, color="white", symbol="circle"),
            name="Sample Feature",
            legendgroup="sample_feature",
            showlegend=True,  # ✅ Always visible
            hoverinfo="skip",
            visible=True,  # ✅ Always visible, not toggled
        )
    )

    # ✅ Strip whitespace from column names
    adjusted_df.columns = adjusted_df.columns.str.strip()

    # ✅ Extract sample intensity column names
    sample_columns = [col.strip() for col in adjusted_df.columns if ".d" in col]

    symbols = []  # ✅ Store marker symbols

    # ✅ Debug print to check Classification Types
    print("\n[DEBUG] Unique 'Classification Type' values in filtered_IM_group:")
    print(filtered_IM_group["Classification Type"].unique())

    # ✅ Group by GroupID to draw trendlines and points
    for idx, (group_id, group_df) in enumerate(filtered_IM_group.groupby("GroupID")):
        # ✅ Extract x (m/z) and y (CCS) for linear fit
        mz_values = group_df["m/z"].values
        ccs_values = group_df["CCS"].values

        # ✅ Perform linear regression for trendline
        slope, intercept, r_value, p_value, _ = stats.linregress(mz_values, ccs_values)

        # ✅ Compute trendline points
        reg_line_x = np.linspace(min(mz_values), max(mz_values), 100)
        reg_line_y = slope * reg_line_x + intercept

        # ✅ Assign a unique legend group for each series
        legend_group_name = f"group_{group_id}"
        series_color = "yellow"  # Customize color if needed

        # 🔹 Add trendline
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Homologous Series {idx + 1}",
                line=dict(color=series_color, dash="dash"),
                legendgroup=legend_group_name,
                hoverinfo="skip",
                visible="legendonly",  # Hidden until toggled
                showlegend=False,
            )
        )

        # ✅ Prepare hover metadata for each point
        hover_texts = []
        for _, row in group_df.iterrows():
            match_name = row.get("Match", "No Match")
            classification = row.get("Classification Type", "Unknown")
            RT = row.get("RT", "N/A")
            repeating_unit = row.get("Repeating Unit", "N/A")
            match_source = row.get("Match Source", "Unknown Source")
            if classification == "N/A":
                classification = match_source  # ✅ Use Library Match instead
            is_library_match = match_source == library_match_source
            marker_symbol = "x" if is_library_match else "circle"
            symbols.append(marker_symbol)

            # ✅ Extract sample-related information (Only for sample features)

            # ✅ Extract sample information (Only for dataset points)
            sample_info = []
            if not is_library_match:  # ❌ Skip sample info for library matches
                sample_columns = [
                    col for col in adjusted_df.columns if ".d.DeMP" in col
                ]
                sample_info = [
                    f"{col.strip()}: {row.get(col.strip(), float('nan')):.2f}"
                    for col in sample_columns
                    if col.strip()
                    in row.index  # ✅ Ensures the column exists before accessing
                    and pd.notna(row.get(col.strip(), float("nan")))
                    and row.get(col.strip(), float("nan")) > 0
                ]
                print(f"[DEBUG] Available columns in row: {list(row.index)}")
                print(f"[DEBUG] Sample columns being accessed: {sample_columns}")

            sample_text = "<br>".join(sample_info) if sample_info else "None"

            # ✅ Construct hover text, excluding "Samples" for library matches
            hover_text = (
                f"Match: {match_name}<br>"
                f"m/z: {row['m/z']:.4f}<br>"
                f"CCS: {row['CCS']:.2f}<br>"
                f"RT: {RT}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}<br>"
            )

            if not is_library_match:
                hover_text += (
                    f"Samples:<br>{sample_text}"  # ✅ Only add for dataset points
                )

            hover_texts.append(hover_text)

        # 🔹 Overlay main homologous series points with metadata
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=ccs_values,
                mode="markers",
                marker=dict(size=10, color=series_color, symbol=symbols),
                name=f"Homologous Series {idx + 1}",
                legendgroup=legend_group_name,
                showlegend=True,
                visible="legendonly",
                text=hover_texts,  # ✅ Full metadata in hover
                hovertemplate="%{text}<extra></extra>",  # ✅ Injects metadata dynamically
            )
        )

        # ✅ Format Plotly Layout
    fig.update_layout(
        title=dict(
            text="CCS vs <i>m/z</i> Trend Analysis",
            font=dict(size=20, color="white", weight="bold"),
            x=0.1,  # Centering the title
            y=0.95,
            xanchor="left",
            yanchor="top",
        ),
        xaxis=dict(
            title=r"<b><i>m/z</i></b>",  # ✅ Bold and italicized using HTML
            title_font=dict(size=16, color="white"),
            tickfont=dict(size=14, color="white", weight="bold"),  # ✅ Tick labels
        ),
        yaxis=dict(
            title="<b>CCS (&#8491;<sup>2</sup>)</b>",
            title_font=dict(size=16, color="white"),
            tickfont=dict(size=14, color="white", weight="bold"),  # ✅ Tick labels
        ),
        template="plotly_dark",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
    )

    return fig


def external_mz_library_matching(IM_group, library_match_source):
    """
    Filters IM_group to retain only groups where at least 2 rows come from the external library file.

    Parameters:
    - IM_group (pd.DataFrame): Data containing identified homologous series.
    - library_match_source (str): The dynamically extracted standards library filename.

    Returns:
    - pd.DataFrame: Filtered IM_group containing only valid groups.
    """
    if IM_group.empty:
        print("[WARNING] IM_group is empty. No filtering applied.")
        return IM_group

    valid_groups = []

    # ✅ Group by GroupID
    for group_id, group_df in IM_group.groupby("GroupID"):
        # ✅ Count how many rows come from the specified external file
        source_count = (group_df["Match Source"] == library_match_source).sum()

        # ✅ Keep groups that have at least 2 rows from the external file
        if source_count >= 2:
            valid_groups.append(group_df)

    # ✅ Combine all valid groups into a new DataFrame
    if valid_groups:
        filtered_IM_group = pd.concat(valid_groups, ignore_index=True)
        print(f"[INFO] {len(filtered_IM_group)} rows retained after filtering.")
    else:
        filtered_IM_group = pd.DataFrame()
        print("[WARNING] No groups met the criteria of at least 2 library matches.")

    return filtered_IM_group


def stack_library_with_adjusted():
    """Loads, standardizes, and combines rows from adjusted_df and library_df into a single DataFrame."""

    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] Data file not found: {FILE_PATH}")
        return None

    if not os.path.exists(LIBRARY_PATH):
        print(f"[ERROR] Library file not found: {LIBRARY_PATH}")
        return None

    # Read both DataFrames
    adjusted_df = pd.read_csv(FILE_PATH)
    library_df = pd.read_csv(LIBRARY_PATH)

    # ✅ Define column mappings to match adjusted_df
    column_mapping = {
        "PrecursorMz": "m/z",
        "PrecursorCCS": "CCS",
        "PrecursorRT": "RT",
        "Name": "Match",
    }

    # ✅ Rename columns in library_df to match adjusted_df
    library_df = library_df.rename(columns=column_mapping)

    # ✅ Add missing columns in `library_df` and fill with "N/A"
    missing_columns = [
        col for col in adjusted_df.columns if col not in library_df.columns
    ]
    for col in missing_columns:
        library_df[col] = "N/A"  # Fill missing columns with a placeholder

    # ✅ Ensure column order matches
    library_df = library_df[adjusted_df.columns]

    # ✅ Assign "Match Source" column
    if "Match Source" in adjusted_df.columns:
        library_df["Match Source"] = LIBRARY_MATCH_SOURCE  # Use extracted filename
    else:
        print("[WARNING] 'Match Source' column not found in adjusted_df.")

    # ✅ Stack the two DataFrames (Concatenation of Rows)
    stacked_df = pd.concat([adjusted_df, library_df], ignore_index=True)

    return stacked_df


import plotly.io as pio


def main():
    """Stacks data, runs analysis, and plots CCS vs. m/z."""
    stacked_df = stack_library_with_adjusted()

    if stacked_df is None:
        print("[ERROR] Could not generate stacked DataFrame. Exiting.")
        return

    print(f"[INFO] Stacked DataFrame created with {len(stacked_df)} rows.")

    # ✅ Extract standards library name
    library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
    print(f"[INFO] Using standards library: {library_match_source}")

    # ✅ Perform Repeating Unit Analysis
    mass_groups = mz_repeating_unit_analysis(
        stacked_df, repeating_units=list(selected_repeating_units.keys())
    )

    if mass_groups.empty:
        print("[WARNING] No homologous series detected. Exiting.")
        return

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")

    # ✅ Run CCS_v_mz_analysis and store IM groups
    filtered_IM_groups = []
    for group_id, group_df in mass_groups.groupby("GroupID"):
        print(f"\n[DEBUG] Analyzing Group {group_id}...")

        IM_group, _, _, _ = CCS_v_mz_analysis(group_df)

        if IM_group:
            IM_group_df = group_df[
                group_df[["m/z", "CCS"]].apply(tuple, axis=1).isin(IM_group)
            ]

            # ✅ Filter IM groups using external standards check
            filtered_IM_group = external_mz_library_matching(
                IM_group_df, library_match_source
            )

            if not filtered_IM_group.empty:
                filtered_IM_groups.append(filtered_IM_group)
                print(filtered_IM_group.head(10).to_string(index=False))

    # ✅ Merge all valid IM groups into one DataFrame
    final_IM_group = (
        pd.concat(filtered_IM_groups, ignore_index=True)
        if filtered_IM_groups
        else pd.DataFrame()
    )

    print("\n[DEBUG] Unique values in 'Classification Type':")
    print(final_IM_group["Classification Type"].unique())
    # ✅ Generate and Show Plot
    fig = make_plotly_graph(stacked_df, final_IM_group, library_match_source)
    pio.show(fig)  # Display interactive plot


if __name__ == "__main__":
    main()
