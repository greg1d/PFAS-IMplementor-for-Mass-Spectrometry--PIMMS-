import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import plotly.graph_objects as go
import webview
import numpy as np


def create_interactive_figure(
    summary_df, pfas_boundary_path, contour_boundary_path, grid_data_path
):
    """
    Creates a highly customized interactive Plotly scatter plot with a shaded undefined region.
    """
    # --- 1. SETUP AND DATA PREPARATION ---
    fig = go.Figure()

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
            "Classification_Type",
            "Peak_mz_1",
            "Intensity_1",
            "PIMMS_CCS",
            "Peak_mz_2",
            "Intensity_2",
            "Intensity_3",
            "Kaufman_C",
            "m_over_C",
            "mass_defect",
            "md_over_C",
            "Short_Match_ID",
        }
        sample_cols = sorted([c for c in df.columns if c not in non_sample_cols])

        for i, row in df.iterrows():
            text = ""
            if "Classification_Type" in row and pd.notna(row["Classification_Type"]):
                text += f"<b>Classification:</b> {row['Classification_Type']}<br>"
            if "PIMMS_CCS" in row and pd.notna(row["PIMMS_CCS"]):
                text += f"<b>PIMMS_CCS:</b> {row['PIMMS_CCS']:.2f}<br>"
            if "Peak_mz_1" in row and pd.notna(row["Peak_mz_1"]):
                text += f"<b>Peak_mz_1:</b> {row['Peak_mz_1']:.4f}<br>"

            text += "<br><b>--- Intensities (> 0) ---</b><br>"
            has_intensity = any(col in row and row[col] > 0 for col in sample_cols)
            if has_intensity:
                for col in sample_cols:
                    if col in row and row[col] > 0:
                        text += f"<b>{col}:</b> {row[col]:,.0f}<br>"
            else:
                text += "Not detected in any sample<br>"
            custom_hover_texts.append(text)
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
    if "Classification_Type" in summary_df.columns:
        for classification, color in color_map.items():
            df_subset = summary_df[summary_df["Classification_Type"] == classification]
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
                name="CF Line",
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

    try:
        if os.path.exists(pfas_boundary_path):
            bdf = pd.read_csv(pfas_boundary_path)
            fig.add_trace(
                go.Scatter(
                    x=bdf["m/C"],
                    y=bdf["MD/C"],
                    mode="lines",
                    line=dict(color="red", dash="dash", width=2),
                    name="PFAS 90% KDE",
                    hoverinfo="none",
                    visible="legendonly",
                )
            )
    except Exception as e:
        print(f"Could not plot PFAS boundary: {e}")

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

    # --- 3. FINAL LAYOUT ---
    fig.update_layout(
        title="Interactive Kaufman Plot of Aligned Features",
        xaxis_title="Average m / C",
        yaxis_title="Average md / C",
        template="plotly_white",
        legend_title_text="Classification",
        plot_bgcolor="#E5E5E5",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )
    return fig


# --- Main Application Class (Unchanged) ---
class PlotLauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plot Launcher")
        self.geometry("350x150")
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Generate the interactive Kaufman plot.").pack(
            pady=10
        )
        ttk.Button(
            main_frame, text="Launch Interactive Plot", command=self.launch_plot
        ).pack(pady=10)

    def launch_plot(self):
        summary_path = r"PIMMS v1.2\import folder\summary_table.csv"
        pfas_boundary_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
        contour_boundary_path = (
            r"PIMMS v1.2\CEF_reading\kaufman_contour_boundaries_SMOOTH.csv"
        )
        grid_data_path = r"PIMMS v1.2\CEF_reading\kaufman_grid_data.npz"

        if not os.path.exists(summary_path):
            messagebox.showerror("Error", f"File not found:\n{summary_path}")
            return
        try:
            summary_df = pd.read_csv(summary_path)
            fig = create_interactive_figure(
                summary_df, pfas_boundary_path, contour_boundary_path, grid_data_path
            )
            if fig:
                html_content = fig.to_html(include_plotlyjs="cdn")
                self.destroy()
                webview.create_window(
                    "Interactive Kaufman Plot", html=html_content, width=900, height=700
                )
                webview.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or plot data:\n{e}")


if __name__ == "__main__":
    app = PlotLauncherApp()
    app.mainloop()
