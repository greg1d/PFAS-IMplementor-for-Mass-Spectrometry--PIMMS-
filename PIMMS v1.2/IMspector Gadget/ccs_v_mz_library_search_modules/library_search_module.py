import os
import sys

import cmocean
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)

# ✅ Ensure `config.py` is properly located
try:
    from config import FILE_PATH
except ModuleNotFoundError:
    print("[ERROR] Could not import `FILE_PATH` from config.py!")
    sys.exit(1)

# ✅ Ensure uploaded library is used if available
UPLOAD_FOLDER = "PIMMS v1.2/imported_libraries"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_library_path():
    """Checks if an uploaded library file exists, otherwise returns the default LIBRARY_PATH."""
    uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".csv")]

    if uploaded_files:
        latest_library = max(
            [os.path.join(UPLOAD_FOLDER, f) for f in uploaded_files],
            key=os.path.getctime,
        )
        return latest_library  # ✅ Use the latest uploaded file
    else:
        print(f"[INFO] No uploaded library found. Using default: {LIBRARY_PATH}")
        return LIBRARY_PATH  # ✅ Fallback to default


# ✅ Use the selected library path
LIBRARY_PATH = get_library_path()
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
SELECTED_UNITS = ["CH2CF2"]
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
NUM_SERIES = 10  # Adjust based on the number of homologous series
HOMOLOGOUS_SERIES_COLORS = cmocean.cm.phase(np.linspace(0, 1, NUM_SERIES))


def library_search_plotly(adjusted_df, filtered_IM_group, library_match_source):
    if filtered_IM_group.empty:
        print("[INFO] No homologous series found. Returning blank graph.")
        fig = go.Figure()
        fig.update_layout(
            title="CCS vs. m/z (No Homologous Series Found)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
            template="plotly_dark",
        )
        return fig

    fig = go.Figure()

    # ✅ Dummy trace for "External Library Match" (X)
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy point (does not appear in the plot)
            y=[None],
            mode="markers",
            marker=dict(size=15, color="white", symbol="x"),
            name="<b>External Library Match</b>",
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
            marker=dict(size=15, color="white", symbol="circle"),
            name="<b>Sample Feature</b>",
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

        series_color = f"rgb({HOMOLOGOUS_SERIES_COLORS[idx % NUM_SERIES][0] * 255}, {HOMOLOGOUS_SERIES_COLORS[idx % NUM_SERIES][1] * 255}, {HOMOLOGOUS_SERIES_COLORS[idx % NUM_SERIES][2] * 255})"
        legend_group_name = f"group_{group_id}"

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
        symbols = []
        for _, row in group_df.iterrows():
            match_name = row.get("Match", "No Match")
            classification = row.get("Classification Type", "Unknown")
            RT = row.get("RT", "N/A")  # Safely access RT
            repeating_unit = row.get("Repeating Unit", "N/A")
            match_source = row.get("Match Source", "Unknown Source")

            # ✅ Assign marker symbol
            marker_symbol = "x" if classification == "External Library" else "circle"
            symbols.append(marker_symbol)

            # ✅ Extract m/z of the current row
            mz_value = row["m/z"]
            matched_row = adjusted_df.loc[adjusted_df["m/z"] == mz_value]

            # ✅ Extract sample intensity values
            sample_info = []
            if not matched_row.empty:
                for col in sample_columns:
                    col = col.strip()  # Remove whitespace

                    if col in matched_row:
                        val = matched_row[col].values[0]  # Extract intensity

                        try:
                            val = float(val)  # Convert to float
                            if pd.notna(val) and val >= 0.001:  # Check valid value
                                sample_info.append(
                                    f"{col}: {val:.2f}"
                                )  # Format to 2 SF
                        except ValueError:
                            print(
                                f"[WARNING] Could not convert value {val} in column {col} to float."
                            )

            sample_text = "<br>".join(sample_info) if sample_info else "None"

            # ✅ Construct hover text
            hover_text = (
                f"Match: {match_name}<br>"
                f"m/z: {row['m/z']:.4f}<br>"
                f"CCS: {row['CCS']:.2f}<br>"
                f"RT: {RT}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}"
            )

            # ✅ Only add samples if NOT External Library
            if classification != "External Library":
                hover_text += f"<br>Samples:<br>{sample_text}"

            hover_texts.append(hover_text)

        # 🔹 Overlay main homologous series points with metadata
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=ccs_values,
                mode="markers+text",
                marker=dict(size=15, color=series_color, symbol=symbols),
                name=f"Homologous Series {idx + 1}",
                legendgroup=legend_group_name,
                showlegend=False,
                visible="legendonly",
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

        # 🔹 Add a separate text-only legend entry (NO MARKER)
        fig.add_trace(
            go.Scatter(
                x=[None],  # Dummy point (does not appear in the plot)
                y=[None],
                mode="lines",  # ✅ Ensures no marker appears
                text=[f"<b>Homologous Series {idx + 1}</b>"],  # ✅ Bold text
                line=dict(
                    color=series_color, dash="dash", width=2
                ),  # ✅ Dashed line with the correct color
                textfont=dict(
                    size=14, color=series_color
                ),  # ✅ Match homologous series color
                name=f"<b>Homologous Series {idx + 1}</b>",  # ✅ Ensure text appears in legend
                legendgroup=legend_group_name,
                showlegend=True,  # ✅ Show this in the legend
            )
        )

        # ✅ Format Plotly Layout
    fig.update_layout(
        xaxis=dict(
            title=r"<b><i>m/z</i></b>",  # ✅ Bold and italicized using HTML
        ),
        yaxis=dict(
            title="<b>CCS (&#8491;<sup>2</sup>)</b>",
        ),
        template="plotly_dark",
    )

    return fig


def external_mz_library_matching(IM_group, library_match_source):
    """
    Filters IM_group to retain only groups where:
    - At least 2 rows come from the external library file.
    - No more than 2 consecutive external library matches before a sample appears.
    - Each homologous series contains at least one sample result.

    Parameters:
    - IM_group (pd.DataFrame): Data containing identified homologous series.
    - library_match_source (str): The dynamically extracted standards library filename.

    Returns:
    - pd.DataFrame: Filtered IM_group containing only valid groups.
    """
    if IM_group.empty:
        return IM_group

    valid_groups = []
    print("IM_group", IM_group)
    # ✅ Group by GroupID
    for group_id, group_df in IM_group.groupby("GroupID"):
        # ✅ Identify external library matches based on classification
        group_df["Is_External_Library"] = ~group_df["Classification Type"].isin(
            ["unmatched", "likely", "tentative"]
        )
        source_count = group_df["Is_External_Library"].sum()

        # ✅ Count the number of non-library samples
        sample_count = len(group_df) - source_count
        print("source_count", source_count)
        print("sample_count", sample_count)
        # ✅ Ensure there is at least one sample in the group
        if source_count >= 2 and sample_count >= 1:
            # ✅ Track consecutive standards
            consecutive_standards = 0
            valid_rows = []
            has_sample = False  # ✅ Track if at least one sample exists

            for _, row in group_df.iterrows():
                is_standard = row["Match Source"] == library_match_source

                if is_standard:
                    consecutive_standards += 1
                else:
                    consecutive_standards = 0  # Reset counter if we find a sample
                    has_sample = True  # ✅ Found at least one sample

                # ✅ Allow max 2 consecutive standards before a sample
                if consecutive_standards <= 2:
                    valid_rows.append(row)

            # ✅ If at least one sample is present, keep this homologous series
            if has_sample:
                valid_groups.append(pd.DataFrame(valid_rows))

    # ✅ Combine all valid groups into a new DataFrame
    if valid_groups:
        filtered_IM_group = pd.concat(valid_groups, ignore_index=True)
    else:
        filtered_IM_group = pd.DataFrame()
    print("filtered IM Group from within the library search module", filtered_IM_group)
    return filtered_IM_group


import os

from config import FILE_PATH, UPLOAD_FOLDER  # Ensure paths are correctly imported

UPLOAD_FOLDER = "PIMMS v1.2/imported_libraries"


def get_latest_library_file():
    """Retrieve the latest uploaded library file from the import folder."""
    try:
        files = [
            os.path.join(UPLOAD_FOLDER, f)
            for f in os.listdir(UPLOAD_FOLDER)
            if f.endswith(".csv")
        ]
        if not files:
            print("[WARNING] No library file found in import folder!")
            return None

        latest_file = max(files, key=os.path.getctime)  # Get the most recent file
        return latest_file

    except Exception as e:
        print(f"[ERROR] Exception while getting latest library file: {e}")
        return None


# ✅ Ensure `LIBRARY_PATH` is dynamically set before calling `plot_figure_2`
LIBRARY_PATH = get_latest_library_file()


def stack_library_with_adjusted():
    """
    Loads, standardizes, and combines rows from adjusted_df and the latest uploaded library_df.

    Returns:
        pd.DataFrame: The combined dataset, or None if there is an issue.
    """

    # ✅ Ensure adjusted data exists
    if not os.path.exists(FILE_PATH):
        print("[ERROR] Adjusted dataset not found. Exiting stacking process.")
        return None

    # ✅ Get the latest uploaded library file
    library_path = get_latest_library_file()
    if library_path is None:
        print("[WARNING] No uploaded library found. Returning only adjusted dataset.")
        return pd.read_csv(FILE_PATH)  # ✅ Return only the adjusted dataset

    # ✅ Read both DataFrames
    print(f"[INFO] Reading adjusted dataset from: {FILE_PATH}")
    adjusted_df = pd.read_csv(FILE_PATH)

    print(f"[INFO] Reading library dataset from: {library_path}")
    library_df = pd.read_csv(library_path)

    # ✅ Standardize column names in the library dataset
    column_mapping = {
        "PrecursorMz": "m/z",
        "PrecursorCCS": "CCS",
        "PrecursorRT": "RT",
        "PrecursorName": "Match",
    }
    library_df = library_df.rename(columns=column_mapping)

    # ✅ Drop unnecessary columns if they exist
    columns_to_drop = ["CAS", "PrecursorCharge", "PrecursorFormula", "MoleculeGroup"]
    library_df = library_df.drop(
        columns=[col for col in columns_to_drop if col in library_df.columns],
        errors="ignore",
    )

    # ✅ Handle missing "PrecursorName" and "PrecursorAdduct"
    if "PrecursorName" in library_df.columns:
        library_df = library_df.drop(columns=["PrecursorName"])
    if "PrecursorAdduct" in library_df.columns:
        library_df["Match"] = (
            library_df["Match"] + " (" + library_df["PrecursorAdduct"] + ")"
        )
        library_df = library_df.drop(columns=["PrecursorAdduct"])

    # ✅ Fill missing values
    library_df = library_df.dropna(axis=1, how="any")

    # ✅ Insert unique ID for library entries
    library_df.insert(0, "ID", range(100000, 100000 + len(library_df)))

    # ✅ Ensure necessary metadata columns are present
    if "Match Source" not in library_df.columns:
        library_df["Match Source"] = os.path.basename(library_path)  # ✅ Use filename
    if "Classification Type" not in library_df.columns:
        library_df["Classification Type"] = "External Library"

    # ✅ Arrange columns in a specific order
    column_order = ["Match", "Match Source", "Classification Type", "ID", "RT", "CCS"]
    remaining_columns = [col for col in library_df.columns if col not in column_order]
    library_df = library_df[column_order + remaining_columns]

    # ✅ Stack the two DataFrames (Concatenation of Rows)
    stacked_df = pd.concat([adjusted_df, library_df], ignore_index=True)
    stacked_df = stacked_df.fillna(0)

    # ✅ Drop additional error-related columns if they exist
    extra_columns_to_drop = ["Mass Error (ppm)", "CCS Error (%)", "RT Error (%)"]
    stacked_df = stacked_df.drop(
        columns=[col for col in extra_columns_to_drop if col in stacked_df.columns],
        errors="ignore",
    )

    # ✅ Save for debugging
    return stacked_df


import plotly.io as pio


def main():
    """Stacks data, runs analysis, and plots CCS vs. m/z."""
    stacked_df = stack_library_with_adjusted()

    if stacked_df is None:
        return

    # ✅ Extract standards library name
    library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

    # ✅ Perform Repeating Unit Analysis
    mass_groups = mz_repeating_unit_analysis(stacked_df, selected_repeating_units)

    if mass_groups.empty:
        return

    # ✅ Run CCS_v_mz_analysis and store IM groups
    filtered_IM_groups = []
    for group_id, group_df in mass_groups.groupby("GroupID"):
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

    # ✅ Merge all valid IM groups into one DataFrame
    final_IM_group = (
        pd.concat(filtered_IM_groups, ignore_index=True)
        if filtered_IM_groups
        else pd.DataFrame()
    )

    # ✅ Generate and Show Plot
    fig = library_search_plotly(stacked_df, final_IM_group, library_match_source)
    pio.show(fig)  # Display interactive plot


if __name__ == "__main__":
    main()
