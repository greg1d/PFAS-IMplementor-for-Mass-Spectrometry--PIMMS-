import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import plotly.express as px
import webview
import numpy as np  # <-- Make sure to add this import


def create_interactive_figure(summary_df, boundary_csv_path):
    """
    Creates a highly customized interactive Plotly scatter plot with line overlays.
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

    # --- 3. NEW: Add CF and CHF Lines ---
    if not summary_df.empty and "m_over_C" in summary_df.columns:
        m_CF, intercept_CF = -8.40596e-05, 0.0010087
        m_CHF, intercept_CHF = -0.0005237, 0.0229902

        x_range = np.linspace(
            summary_df["m_over_C"].min(), summary_df["m_over_C"].max(), 100
        )
        y_CF = m_CF * x_range + intercept_CF
        y_CHF = m_CHF * x_range + intercept_CHF

        fig.add_scatter(
            x=x_range,
            y=y_CF,
            mode="lines",
            line=dict(color="purple", width=2, dash="dot"),
            name="CF Line",
            hoverinfo="skip",
        )
        fig.add_scatter(
            x=x_range,
            y=y_CHF,
            mode="lines",
            line=dict(color="green", width=2, dash="dashdot"),
            name="CHF Line",
            hoverinfo="skip",
        )
        print("Overlaying CF and CHF trend lines.")
    # --- End of New Code ---

    # 4. Overlay the boundary file
    try:
        if os.path.exists(boundary_csv_path):
            boundary_df = pd.read_csv(boundary_csv_path)
            fig.add_scatter(
                x=boundary_df["m/C"],
                y=boundary_df["MD/C"],
                mode="lines",
                line=dict(color="red", dash="dash", width=2),
                name="PFAS 90% KDE Boundary",
                hoverinfo="skip",
            )
    except Exception as e:
        print(f"[ERROR] Could not plot boundary file: {e}")

    # 5. Final layout and styling
    fig.update_layout(template="plotly_white", legend_title_text="Classification")
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
        boundary_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
        if not os.path.exists(summary_path):
            messagebox.showerror("Error", f"File not found:\n{summary_path}")
            return
        try:
            summary_df = pd.read_csv(summary_path)
            fig = create_interactive_figure(summary_df, boundary_path)
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
