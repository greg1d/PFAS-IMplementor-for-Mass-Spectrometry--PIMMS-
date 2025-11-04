import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression


class PlotWidget(ttk.Frame):
    """A self-contained widget for displaying the Matplotlib plot."""

    def __init__(self, parent):
        super().__init__(parent)

        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.update_plot(None, None)  # Draw initial empty state

    def update_plot(self, context_df, highlighted_df):
        """
        Clears and redraws the plot, using different markers for library vs. sample points.
        """
        self.ax.clear()

        # Plot the full parent group (context) in gray if it exists
        if context_df is not None and not context_df.empty:
            gray_df = context_df.copy()

            # Exclude points that are External Standards in highlighted_df
            if highlighted_df is not None and not highlighted_df.empty:
                standards_df = highlighted_df[
                    highlighted_df["Classification Type"] == "External Standard"
                ]
                if not standards_df.empty:
                    gray_df = gray_df[~gray_df.index.isin(standards_df.index)]

            if not gray_df.empty:
                parent_id = int(gray_df["GroupID"].iloc[0])
                self.ax.scatter(
                    gray_df["m/z"],
                    gray_df["CCS"],
                    color="lightgray",
                    s=30,
                    label=f"_Parent Group {parent_id}",
                )

        # Plot the selected trend in color with a line
        if highlighted_df is not None and not highlighted_df.empty:
            trend_id = highlighted_df["trend_group"].iloc[0]

            # Split data by Classification Type
            standards_df = highlighted_df[
                highlighted_df["Classification Type"] == "External Standard"
            ]
            other_points_df = highlighted_df[
                highlighted_df["Classification Type"] != "External Standard"
            ]

            # Plot non-standards as circles (o)
            if not other_points_df.empty:
                self.ax.scatter(
                    other_points_df["m/z"],
                    other_points_df["CCS"],
                    marker="o",
                    color="blue",
                    s=50,
                    label="Sample Feature",
                )

            # Plot standards as crosses (x) ONLY, no underlying points
            if not standards_df.empty:
                self.ax.scatter(
                    standards_df["m/z"],
                    standards_df["CCS"],
                    marker="x",
                    color="red",
                    s=80,
                    label="External Standard",
                    zorder=5,  # ensure they are on top
                )

            # Fit a model to the ENTIRE highlighted group and plot the trend line
            model = LinearRegression().fit(
                highlighted_df[["m/z"]].values, highlighted_df["CCS"].values
            )
            x_range = np.linspace(
                highlighted_df["m/z"].min(), highlighted_df["m/z"].max(), 100
            )
            y_pred = model.predict(x_range.reshape(-1, 1))
            self.ax.plot(
                x_range,
                y_pred,
                linestyle="--",
                color="black",
                label=f"Trend {trend_id} Fit",
                zorder=0,
            )

            self.ax.set_title(f"Viewing Trend {trend_id}")
        else:
            self.ax.text(
                0.5,
                0.5,
                "Load data and run analysis to view trends.",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
            )
            self.ax.set_title("Analysis Viewer")

        self.ax.set_xlabel("m/z")
        self.ax.set_ylabel("CCS ($Å^2$)")
        self.ax.grid(True)

        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            self.ax.legend()

        self.fig.tight_layout()
        self.canvas.draw()
