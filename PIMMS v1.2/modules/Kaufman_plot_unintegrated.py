from tkinter import messagebox
import pandas as pd
import os
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import interpn  # Required for the new calculation
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    get_cef_sample_names,
    compute_kaufman_constants,
    run_matching_pipeline,
)
from calculating_Kaufman_parameters_file_2 import (
    align_features,
    create_summary_table,
)


def calculate_and_classify_ratio(summary_df, grid_data_path):
    """
    Calculates the 'Predicted C/F ratio' by interpolating from the grid,
    then classifies each feature and formats the column for display.
    """
    try:
        grid_data = np.load(grid_data_path)
        X, Y, Z_smoothed = grid_data["X"], grid_data["Y"], grid_data["Z_smoothed"]
    except FileNotFoundError:
        print(f"ERROR: Grid data file not found at {grid_data_path}.")
        return None

    # Interpolate the Z-value for each point from the smoothed grid
    points_to_check = summary_df[["md_over_C", "m_over_C"]].values
    interpolated_z_values = interpn(
        (Y[:, 0], X[0, :]),
        Z_smoothed,
        points_to_check,
        method="linear",
        bounds_error=False,
        fill_value=np.nan,
    )
    summary_df["Predicted C/F ratio"] = interpolated_z_values

    # --- CORRECTED LOGIC ORDER ---

    # 1. Define the condition for being "out of bounds"
    out_of_bounds_condition = (summary_df["Predicted C/F ratio"].isna()) | (
        summary_df["Predicted C/F ratio"] < 0.8
    )

    # 2. Explicitly change the column's data type to 'object' FIRST.
    #    This prepares it to accept a mix of numbers and strings.
    summary_df["Predicted C/F ratio"] = summary_df["Predicted C/F ratio"].astype(object)

    # 3. Use .loc to insert the "out of bounds" string.
    #    The original NaN and float values are still present at this point.
    summary_df.loc[out_of_bounds_condition, "Predicted C/F ratio"] = "out of bounds"

    # 4. NOW, round the remaining numerical values in the column.
    #    We can use .apply() to safely round only the numbers and leave the strings untouched.
    summary_df["Predicted C/F ratio"] = summary_df["Predicted C/F ratio"].apply(
        lambda x: round(x, 1) if isinstance(x, (int, float)) else x
    )
    # --- End of Correction ---

    return summary_df


def create_interactive_figure(summary_df, contour_boundary_path, grid_data_path):
    """
    Creates a highly customized interactive Plotly scatter plot with a shaded undefined region.
    """
    # --- 1. SETUP AND DATA PREPARATION ---
    fig = go.Figure()
    # --- DEBUG ---
    print("\n--- DEBUG: START of create_interactive_figure ---")
    print("Initial summary_df columns:", summary_df.columns.tolist())
    print("First 2 rows of summary_df:\n", summary_df.head(2))
    # --- END DEBUG ---
    try:
        grid_data = np.load(grid_data_path)
        X, Y, Z_smoothed = grid_data["X"], grid_data["Y"], grid_data["Z_smoothed"]
    except FileNotFoundError:
        messagebox.showerror(
            "Error",
            f"Grid data file not found at {grid_data_path}.\nPlease run the calculation script first.",
        )
        return None

    # Helper function to build the detailed hover text for a given dataframe
    def build_hover_text(df):
        custom_hover_texts = []
        non_sample_cols = {
            "AlignmentID",
            "Match_ID",
            "Classification Type",
            "Peak_mz_1",
            "Intensity_1",
            "PIMMS_CCS",
            "DT_PIMMS",
            "RT_PIMMS",
            "Peak_mz_2",
            "Intensity_2",
            "Intensity_3",
            "Kaufman_C",
            "m_over_C",
            "mass_defect",
            "md_over_C",
            "Short_Match_ID",
            "Predicted C/F ratio",
            "Isotopic_analysis",
            "M/M+2 Distribution",
        }
        sample_cols = sorted([c for c in df.columns if c not in non_sample_cols])
        # --- DEBUG ---
        print("Identified sample_cols:", sample_cols)
        # --- END DEBUG ---

        for i, row in df.iterrows():
            text = ""
            if "Classification Type" in row and pd.notna(row["Classification Type"]):
                text += f"<b>Classification:</b> {row['Classification Type']}<br>"
            if "PIMMS_CCS" in row and pd.notna(row["PIMMS_CCS"]):
                text += f"<b>CCS:</b> {row['PIMMS_CCS']:.2f}<br>"
            if "Peak_mz_1" in row and pd.notna(row["Peak_mz_1"]):
                text += f"<b>m/z:</b> {row['Peak_mz_1']:.4f}<br>"
            if "DT_PIMMS" in row and pd.notna(row["DT_PIMMS"]):
                text += f"<b>DT:</b> {row['DT_PIMMS']:.2f}<br>"
            if "RT_PIMMS" in row and pd.notna(row["RT_PIMMS"]):
                text += f"<b>RT:</b> {row['RT_PIMMS']:.2f}<br>"
            # --- MODIFIED: Explicitly format the number to 1 decimal place here ---
            if "Predicted C/F ratio" in row and pd.notna(row["Predicted C/F ratio"]):
                value = row["Predicted C/F ratio"]
                if isinstance(value, (int, float)):
                    # If it's a number, format it to one decimal place
                    text += f"<b>Predicted F/C Ratio:</b> {value:.1f}<br>"
                else:
                    # If it's a string (like "out of bounds"), display it directly
                    text += f"<b>Predicted F/C Ratio:</b> {value}<br>"
            # --- End of Modification ---
            text += "<br><b>--- Intensities (> 0) ---</b><br>"
            has_intensity = any(col in row and row[col] > 0 for col in sample_cols)
            if has_intensity:
                for col in sample_cols:
                    if col in row and row[col] > 0:
                        text += f"<b>{col}:</b> {row[col]:,.0f}<br>"
            else:
                text += "Not detected in any sample<br>"
            custom_hover_texts.append(text)
        if custom_hover_texts:
            print("First generated hover text:\n", custom_hover_texts[0])
        return custom_hover_texts

    # Create the truncated ID column for the hover title
    summary_df["Short_Match_ID"] = summary_df["Match_ID"].apply(
        lambda x: (str(x)[:27] + "...") if len(str(x)) > 30 else str(x)
    )

    # --- 2. ADD PLOT LAYERS (FROM BOTTOM TO TOP) ---

    # Layer 1: Background (white for defined area, grey for undefined)
    fig.add_trace(
        go.Contour(
            x=X[0],
            y=Y[:, 0],
            z=Z_smoothed,
            showscale=False,
            contours_coloring="fill",
            colorscale=[[0, "white"], [1, "white"]],
            hoverinfo="none",
            showlegend=False,
        )
    )

    # Layer 2: Scatter points, colored by classification
    color_map = {"likely": "#648FFF", "tentative": "#DC267F", "unmatched": "#FFB000"}
    if "Classification Type" in summary_df.columns:
        for classification, color in color_map.items():
            df_subset = summary_df[summary_df["Classification Type"] == classification]
            if df_subset.empty:
                continue

            fig.add_trace(
                go.Scatter(
                    x=df_subset["m_over_C"],
                    y=df_subset["md_over_C"],
                    mode="markers",
                    marker=dict(
                        color=color, size=10, line=dict(width=1, color="black")
                    ),
                    name=classification,
                    text=df_subset["Short_Match_ID"],
                    customdata=build_hover_text(df_subset),
                    hovertemplate="<b>%{text}</b><br><br>%{customdata}<extra></extra>",
                )
            )

    # Layer 3: Boundary and Trend Lines
    if not summary_df.empty:
        m_CF, i_CF = -8.40596e-05, 0.0010087
        m_CHF, i_CHF = -0.0005237, 0.0229902
        x_range = np.linspace(
            summary_df["m_over_C"].min(), summary_df["m_over_C"].max(), 100
        )
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=m_CF * x_range + i_CF,
                mode="lines",
                line=dict(color="purple", width=2, dash="dot"),
                name="CF2 Line",
                hoverinfo="none",
                visible="legendonly",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=m_CHF * x_range + i_CHF,
                mode="lines",
                line=dict(color="green", width=2, dash="dashdot"),
                name="CHF Line",
                hoverinfo="none",
                visible="legendonly",
            )
        )
    # Layer 4: Dummy traces for custom legend entries
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="black", width=2, dash="solid"),
            name="Mean F/C ratio for PFAS<br>with %mass F > 50%<sup>1</sup>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                symbol="square",
                color="#E5E5E5",
                size=30,
                line=dict(width=1, color="darkgrey"),
            ),
            name="Region not bound <br>within %mass F > 50%<sup>1</sup>",
            hoverinfo="none",
        )
    )

    # Layer 5: Calculated contour lines with inline labels
    try:
        if os.path.exists(contour_boundary_path):
            cdf = pd.read_csv(contour_boundary_path)
            major_levels = {0.8, 1.0, 1.5, 2.0, 2.5, 3.0}
            grouping_col = "segment_id" if "segment_id" in cdf.columns else "level"
            labeled_levels = set()

            for _, group in cdf.groupby(grouping_col):
                level = group["level"].iloc[0]
                is_major = level in major_levels
                style = (
                    dict(color="black", width=2, dash="solid")
                    if is_major
                    else dict(color="grey", width=1, dash="dash")
                )
                fig.add_trace(
                    go.Scatter(
                        x=group["m/C"],
                        y=group["MD/C"],
                        mode="lines",
                        line=style,
                        name=f"Contour {level}",
                        showlegend=False,
                        hoverinfo="none",
                    )
                )

                if is_major and level not in labeled_levels:
                    mid_index = len(group) // 2
                    label_x = group["m/C"].iloc[mid_index]
                    label_y = group["MD/C"].iloc[mid_index]
                    fig.add_annotation(
                        x=label_x,
                        y=label_y,
                        text=f"<b>{level}</b>",
                        showarrow=False,
                        font=dict(color="black", size=10),
                        bgcolor="rgba(255, 255, 255, 0.7)",
                        borderpad=2,
                    )
                    labeled_levels.add(level)
    except Exception as e:
        print(f"Could not plot calculated contour boundaries: {e}")
    citation_text = "<sup>1</sup>Zweigle, J., Bugsel, B. & Zwiener, <br><i>Anal Bioanal Chem</i>, 415, 1791-1801 (2023). <br>https://doi.org/10.1007/s00216-023-04601-1"
    fig.add_annotation(
        showarrow=False,
        text=citation_text,
        xref="paper",  # Positions relative to the entire figure
        yref="paper",
        x=1.01,  # x=0 is the left edge
        y=0.6,  # y=-0.15 is below the x-axis
        xanchor="left",
        yanchor="top",
        align="left",
        font=dict(size=8, color="grey"),
    )
    # --- 3. FINAL LAYOUT ---
    fig.update_layout(
        title="Interactive Kauffman Plot of Aligned Features",
        xaxis_title="m/C",
        yaxis_title="md/C",
        template="plotly_white",
        legend_title_text="Classification",
        plot_bgcolor="#E5E5E5",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )
    # --- DEBUG ---
    print("--- DEBUG: END of create_interactive_figure. Returning figure object. ---")
    # --- END DEBUG ---
    return fig


def run_full_pipeline(pimms_file_path, cef_folder, status_callback):
    """
    Executes the entire data processing workflow from file inputs to the
    final summary table DataFrame.
    """
    status_callback("Loading PIMMS file...")
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = pimms_df.columns.str.strip()

    status_callback("Parsing all CEF files...")
    all_cef_data = parse_all_cef_files_in_folder(cef_folder)

    status_callback("Pre-calculating Kaufman Constants...")
    kaufman_df = compute_kaufman_constants(all_cef_data)

    status_callback("Running matching and alignment pipeline...")
    sample_names = get_cef_sample_names(cef_folder)
    combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)

    if combined_df.empty:
        status_callback("Pipeline complete: No matches were found.")
        return None

    aligned_df = align_features(combined_df)
    final_long_df = pd.merge(
        aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
    )
    summary_table = create_summary_table(final_long_df)

    return summary_table
