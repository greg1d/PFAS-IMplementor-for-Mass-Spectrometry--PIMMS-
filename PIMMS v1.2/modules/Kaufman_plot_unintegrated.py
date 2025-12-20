import os
from tkinter import messagebox

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interpn

from .calculating_Kaufman_parameters_file_2 import (
    align_features,
    create_summary_table,
)
from .CEF_PIMMS_reader_workflow_file_1 import (
    compute_kaufman_constants,
    get_cef_sample_names,
    parse_all_cef_files_in_folder,
    run_matching_pipeline,
)


def calculate_and_classify_ratio(summary_df, grid_data_path):
    print("\n[DEBUG] --- Entering calculate_and_classify_ratio ---")

    if summary_df is None or summary_df.empty:
        print("[DEBUG] summary_df is empty or None.")
        return None

    # Validation
    if "md_over_C" not in summary_df.columns or "m_over_C" not in summary_df.columns:
        print("[DEBUG] ERROR: Missing 'md_over_C' or 'm_over_C' columns.")
        return None

    try:
        grid_data = np.load(grid_data_path)
        X, Y, Z_smoothed = grid_data["X"], grid_data["Y"], grid_data["Z_smoothed"]
    except FileNotFoundError:
        print(f"[DEBUG] ERROR: Grid data file not found at {grid_data_path}.")
        return None

    # Interpolation
    try:
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
    except Exception as e:
        print(f"[DEBUG] ERROR during interpolation: {e}")
        return summary_df

    # Classification
    out_of_bounds_condition = (summary_df["Predicted C/F ratio"].isna()) | (
        summary_df["Predicted C/F ratio"] < 0.8
    )

    summary_df["Predicted C/F ratio"] = summary_df["Predicted C/F ratio"].astype(object)
    summary_df.loc[out_of_bounds_condition, "Predicted C/F ratio"] = "out of bounds"

    summary_df["Predicted C/F ratio"] = summary_df["Predicted C/F ratio"].apply(
        lambda x: round(x, 1) if isinstance(x, (int, float)) else x
    )

    return summary_df


def create_interactive_figure(summary_df, contour_boundary_path, grid_data_path):
    print("\n[DEBUG] --- Entering create_interactive_figure ---")
    fig = go.Figure()

    if summary_df is None or summary_df.empty:
        return None

    try:
        grid_data = np.load(grid_data_path)
        X, Y, Z_smoothed = grid_data["X"], grid_data["Y"], grid_data["Z_smoothed"]
    except FileNotFoundError:
        messagebox.showerror("Error", f"Grid data not found at {grid_data_path}")
        return None

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
            "Mean_Intensity",
            "Detection_Count",
            "Kaufman_C_StdDev",
        }
        # Identify sample columns by excluding known metadata columns
        sample_cols = sorted(
            [
                c
                for c in df.columns
                if c not in non_sample_cols and not c.endswith("_StdDev")
            ]
        )

        for i, row in df.iterrows():
            text = ""
            if "Classification Type" in row and pd.notna(row["Classification Type"]):
                text += f"<b>Classification:</b> {row['Classification Type']}<br>"
            if "PIMMS_CCS" in row and pd.notna(row["PIMMS_CCS"]):
                text += f"<b>CCS:</b> {row['PIMMS_CCS']:.2f}<br>"
            if "Predicted C/F ratio" in row and pd.notna(row["Predicted C/F ratio"]):
                text += f"<b>Predicted F/C Ratio:</b> {row['Predicted C/F ratio']}<br>"

            text += "<br><b>--- Intensities (> 0) ---</b><br>"
            has_intensity = False
            for col in sample_cols:
                # Ensure column exists and value is numeric/positive
                if col in row and isinstance(row[col], (int, float)) and row[col] > 0:
                    text += f"<b>{col}:</b> {row[col]:,.0f}<br>"
                    has_intensity = True

            if not has_intensity:
                text += "Not detected in any sample<br>"
            custom_hover_texts.append(text)
        return custom_hover_texts

    if "Match_ID" in summary_df.columns:
        summary_df["Short_Match_ID"] = summary_df["Match_ID"].apply(
            lambda x: (str(x)[:27] + "...") if len(str(x)) > 30 else str(x)
        )
    else:
        summary_df["Short_Match_ID"] = "N/A"

    # --- Plot Layers ---
    # 1. Background
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

    # 2. Scatter Points
    color_map = {"likely": "#648FFF", "tentative": "#DC267F", "unmatched": "#FFB000"}
    if "Classification Type" in summary_df.columns:
        for classification, color in color_map.items():
            df_subset = summary_df[summary_df["Classification Type"] == classification]
            if df_subset.empty:
                continue

            # Use 'md_over_C' and 'm_over_C' for coordinates
            if "m_over_C" in df_subset.columns and "md_over_C" in df_subset.columns:
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

    # 3. Boundaries
    if not summary_df.empty and "m_over_C" in summary_df.columns:
        x_range = np.linspace(
            summary_df["m_over_C"].min(), summary_df["m_over_C"].max(), 100
        )
        m_CF, i_CF = -8.40596e-05, 0.0010087
        m_CHF, i_CHF = -0.0005237, 0.0229902

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

    # 4. Legend Items
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="black", width=2, dash="solid"),
            name="Mean F/C ratio for PFAS...",
        )
    )

    # 5. Contours from file
    if os.path.exists(contour_boundary_path):
        try:
            cdf = pd.read_csv(contour_boundary_path)
            major_levels = {0.8, 1.0, 1.5, 2.0, 2.5, 3.0}
            grouping_col = "segment_id" if "segment_id" in cdf.columns else "level"
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
                        showlegend=False,
                        hoverinfo="none",
                    )
                )
        except Exception:
            pass

    fig.update_layout(
        title="Interactive Kaufmann Plot",
        xaxis_title="m/C",
        yaxis_title="md/C",
        template="plotly_white",
        plot_bgcolor="#E5E5E5",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )
    return fig


def run_full_pipeline(pimms_file_path, cef_folder, status_callback):
    """
    Executes the entire data processing workflow.
    CORRECTED: Avoids redundant merging that creates column suffixes (_x, _y).
    """
    print("\n[DEBUG] --- Entering run_full_pipeline ---")

    status_callback("Loading PIMMS file...")
    try:
        pimms_df = pd.read_csv(pimms_file_path)
        pimms_df.columns = pimms_df.columns.str.strip()
    except Exception as e:
        status_callback(f"Error reading PIMMS file: {e}")
        return None

    status_callback("Parsing all CEF files...")
    try:
        all_cef_data = parse_all_cef_files_in_folder(cef_folder)
    except Exception as e:
        status_callback(f"Error parsing CEF files: {e}")
        return None

    status_callback("Running matching and alignment pipeline...")
    sample_names = get_cef_sample_names(cef_folder)

    # Step 1: Run Matching (This now includes Kaufman metrics natively if your File 1 is updated)
    combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)

    if combined_df is None or combined_df.empty:
        status_callback("Pipeline complete: No matches were found.")
        return None

    # Step 2: Check if Kaufman metrics exist
    metrics_exist = (
        "Intensity_1" in combined_df.columns and "Kaufman_C" in combined_df.columns
    )
    print(f"[DEBUG] Kaufman metrics present in combined_df: {metrics_exist}")

    # Step 3: Align Features
    print("[DEBUG] Aligning features...")
    aligned_df = align_features(combined_df)

    # Step 4: Conditional Merge
    # Only calculate and merge kaufman_df if the data ISN'T already there.
    if not metrics_exist:
        print(
            "[DEBUG] Metrics missing. Calculating and merging Kaufman stats manually..."
        )
        status_callback("Calculating Kaufman Constants...")
        kaufman_df = compute_kaufman_constants(all_cef_data)
        final_long_df = pd.merge(
            aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
        )
    else:
        print("[DEBUG] Metrics already present. Skipping redundant merge.")
        final_long_df = aligned_df

    status_callback("Creating summary table...")
    summary_table = create_summary_table(final_long_df)

    # Validation
    if summary_table is not None:
        print(
            f"[DEBUG] Summary table columns: {summary_table.columns.tolist()[:10]}..."
        )
        if "Intensity_1" not in summary_table.columns:
            print(
                "[DEBUG] CRITICAL ERROR: 'Intensity_1' still missing from summary table."
            )

    return summary_table
