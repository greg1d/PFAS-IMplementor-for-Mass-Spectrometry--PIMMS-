import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import plotly.express as px
import webview


def create_interactive_figure(summary_df, boundary_csv_path):
    """
    Creates an interactive Plotly scatter plot with points colored by Classification_Type.
    """
    required_cols = {"m_over_C", "md_over_C", "Match_ID"}
    if not required_cols.issubset(summary_df.columns):
        print(f"[ERROR] Summary table is missing required columns: {required_cols}")
        return None

    # --- NEW: Define color mapping based on your request ---
    color_map = {
        "likely": "#648FFF",  # Blue
        "tentative": "#DC267F",  # Magenta
        "unmatched": "#FFB000",  # Amber
    }

    # Check if the classification column exists to apply coloring
    if "Classification_Type" in summary_df.columns:
        color_args = {
            "color": "Classification_Type",
            "color_discrete_map": color_map,
            "category_orders": {
                "Classification_Type": ["likely", "tentative", "unmatched"]
            },  # Ensures legend order
        }
        print("Applying colors based on 'Classification_Type'.")
    else:
        color_args = {}
        print(
            "[WARNING] 'Classification_Type' column not found. Plotting with default color."
        )
    # --- End of New Code ---

    # 1. Create the main scatter plot, now with dynamic color arguments
    fig = px.scatter(
        summary_df,
        x="m_over_C",
        y="md_over_C",
        hover_name="Match_ID",
        hover_data={col: True for col in summary_df.columns},
        labels={"m_over_C": "Average m / C", "md_over_C": "Average md / C"},
        title="Interactive Kaufman Plot of Aligned Features",
        **color_args,  # Unpack the color arguments here
    )

    # 2. Read and overlay the boundary file
    try:
        if os.path.exists(boundary_csv_path):
            boundary_df = pd.read_csv(boundary_csv_path)
            if {"m/C", "MD/C"}.issubset(boundary_df.columns):
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

    # 3. Update layout and styling
    fig.update_layout(template="plotly_white", legend_title_text="Classification")
    # Use a selector to avoid changing the color of the boundary line
    fig.update_traces(
        marker=dict(size=10, line=dict(width=1, color="black")),
        selector=dict(mode="markers"),
    )

    return fig


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
    # Ensure you have installed pywebview correctly
    # pip install pywebview[tkinter]

    app = PlotLauncherApp()
    app.mainloop()
