import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import plotly.express as px
import webview
import numpy as np


def create_interactive_figure(summary_df, pfas_boundary_path, contour_boundary_path):
    """
    Creates a highly customized interactive Plotly scatter plot with multiple line overlays.
    """
    required_cols = {"m_over_C", "md_over_C", "Match_ID"}
    if not required_cols.issubset(summary_df.columns):
        print("[ERROR] Summary table is missing required columns.")
        return None

    # --- 1. PREPARE HOVER DATA (Conditional text) ---
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
    sample_cols = sorted(
        [col for col in summary_df.columns if col not in non_sample_cols]
    )

    summary_df["Short_Match_ID"] = summary_df["Match_ID"].apply(
        lambda x: (str(x)[:27] + "...") if len(str(x)) > 30 else str(x)
    )

    hover_texts = []
    for index, row in summary_df.iterrows():
        text = ""
        if "Classification_Type" in row and pd.notna(row["Classification_Type"]):
            text += f"<b>Classification:</b> {row['Classification_Type']}<br>"
        if "PIMMS_CCS" in row and pd.notna(row["PIMMS_CCS"]):
            text += f"<b>PIMMS_CCS:</b> {row['PIMMS_CCS']:.2f}<br>"
        if "Peak_mz_1" in row and pd.notna(row["Peak_mz_1"]):
            text += f"<b>Peak_mz_1:</b> {row['Peak_mz_1']:.4f}<br>"
        text += "<br><b>--- Intensities (> 0) ---</b><br>"
        has_intensity = False
        for col in sample_cols:
            if row[col] > 0:
                text += f"<b>{col}:</b> {row[col]:,.0f}<br>"
                has_intensity = True
        if not has_intensity:
            text += "Not detected in any sample<br>"
        hover_texts.append(text)
    summary_df["custom_hover_text"] = hover_texts

    # --- 2. CREATE THE PLOT ---
    color_map = {"likely": "#648FFF", "tentative": "#DC267F", "unmatched": "#FFB000"}
    color_args = (
        {"color": "Classification_Type", "color_discrete_map": color_map}
        if "Classification_Type" in summary_df.columns
        else {}
    )

    fig = px.scatter(
        summary_df,
        x="m_over_C",
        y="md_over_C",
        hover_name="Short_Match_ID",
        custom_data=["custom_hover_text"],
        labels={"m_over_C": "Average m / C", "md_over_C": "Average md / C"},
        title="Interactive Kaufman Plot of Aligned Features",
        **color_args,
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>%{customdata[0]}<extra></extra>"
    )

    # --- 3. OVERLAY LINES (CF, CHF, and PFAS Boundary) ---
    if not summary_df.empty:
        m_CF, i_CF = -8.40596e-05, 0.0010087
        m_CHF, i_CHF = -0.0005237, 0.0229902
        x_range = np.linspace(
            summary_df["m_over_C"].min(), summary_df["m_over_C"].max(), 100
        )
        fig.add_scatter(
            x=x_range,
            y=m_CF * x_range + i_CF,
            mode="lines",
            line=dict(color="purple", width=2, dash="dot"),
            name="CF Line",
            hoverinfo="skip",
        )
        fig.add_scatter(
            x=x_range,
            y=m_CHF * x_range + i_CHF,
            mode="lines",
            line=dict(color="green", width=2, dash="dashdot"),
            name="CHF Line",
            hoverinfo="skip",
        )

    try:
        if os.path.exists(pfas_boundary_path):
            boundary_df = pd.read_csv(pfas_boundary_path)
            fig.add_scatter(
                x=boundary_df["m/C"],
                y=boundary_df["MD/C"],
                mode="lines",
                line=dict(color="red", dash="dash", width=2),
                name="PFAS 90% KDE Boundary",
                hoverinfo="skip",
            )
    except Exception as e:
        print(f"[ERROR] Could not plot PFAS boundary file: {e}")

    # --- 4. OVERLAY THE CALCULATED CONTOUR BOUNDARIES ---
    try:
        if os.path.exists(contour_boundary_path):
            print(
                f"Loading calculated contour boundaries from: {contour_boundary_path}"
            )
            contour_df = pd.read_csv(contour_boundary_path)

            grouping_col = (
                "segment_id" if "segment_id" in contour_df.columns else "level"
            )

            major_levels = {0.8, 1.0, 1.5, 2.0, 2.5, 3.0}
            added_major_levels = set()
            added_minor_levels = set()

            for i, (group_id, group) in enumerate(contour_df.groupby(grouping_col)):
                level = group["level"].iloc[0]

                if level in major_levels:
                    line_color, line_dash, line_width = "black", "solid", 2
                    show_legend = level not in added_major_levels
                    added_major_levels.add(level)
                    name_prefix = "Major Contour "
                else:
                    line_color, line_dash, line_width = "grey", "dash", 1
                    show_legend = level not in added_minor_levels
                    added_minor_levels.add(level)
                    name_prefix = "Minor Contour "

                fig.add_scatter(
                    x=group["m/C"],
                    y=group["MD/C"],
                    mode="lines",
                    line=dict(color=line_color, width=line_width, dash=line_dash),
                    name=f"{name_prefix}Level {level}",
                    legendgroup=f"level_{level}",
                    showlegend=show_legend,
                    hoverinfo="skip",
                )
    except Exception as e:
        print(f"[ERROR] Could not plot calculated contour boundaries: {e}")
    # --- End of Contour Logic ---

    # 5. Final layout and styling
    fig.update_layout(
        template="plotly_white",
        legend_title_text="Legend",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
    )
    fig.update_traces(
        marker=dict(size=10, line=dict(width=1, color="black")),
        selector=dict(mode="markers"),
    )
    return fig


# --- Main Application (Unchanged) ---
class PlotLauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plot Launcher")
        self.geometry("350x150")
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        label = ttk.Label(main_frame, text="Generate the interactive Kaufman plot.")
        label.pack(pady=10)
        plot_button = ttk.Button(
            main_frame, text="Launch Interactive Plot", command=self.launch_plot
        )
        plot_button.pack(pady=10)

    def launch_plot(self):
        summary_path = r"PIMMS v1.2\import folder\summary_table.csv"
        pfas_boundary_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
        contour_boundary_path = (
            "PIMMS v1.2\CEF_reading\kaufman_contour_boundaries_SMOOTH.csv"
        )
        if not os.path.exists(summary_path):
            messagebox.showerror("Error", f"File not found:\n{summary_path}")
            return
        try:
            summary_df = pd.read_csv(summary_path)
            fig = create_interactive_figure(
                summary_df, pfas_boundary_path, contour_boundary_path
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
