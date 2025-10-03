import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class PlotWidget(ttk.Frame):
    """A self-contained widget for displaying the Matplotlib plot."""

    def __init__(self, parent):
        super().__init__(parent)

        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.update_plot(None, None)  # Draw initial empty state

    def update_plot(self, raw_df, analyzed_df):
        """Clears and redraws the Matplotlib plot based on the provided data."""
        self.ax.clear()

        if raw_df is not None:
            self.ax.scatter(
                raw_df["m/z"],
                raw_df["CCS"],
                color="gray",
                alpha=0.2,
                label="All Features",
            )

        if analyzed_df is None or analyzed_df.empty:
            message = (
                "No homologous series found."
                if raw_df is not None
                else "Load a report file to begin."
            )
            self.ax.text(
                0.5, 0.5, message, ha="center", va="center", transform=self.ax.transAxes
            )
        else:
            for group_id, group_data in analyzed_df.groupby("GroupID"):
                self.ax.plot(
                    group_data["m/z"],
                    group_data["CCS"],
                    marker="o",
                    linestyle="-",
                    label=f"Group {group_id}",
                )

        self.ax.set_title("CCS vs. m/z Homologous Series")
        self.ax.set_xlabel("m/z")
        self.ax.set_ylabel("CCS ($Å^2$)")
        self.ax.grid(True)
        self.ax.legend()
        self.fig.tight_layout()
        self.canvas.draw()
