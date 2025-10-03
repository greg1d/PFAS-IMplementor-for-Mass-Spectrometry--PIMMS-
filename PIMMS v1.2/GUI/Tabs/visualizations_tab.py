import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class VisualizationsTab(ttk.Frame):
    """
    A Tkinter Tab that loads data from a fixed CSV and displays a Matplotlib plot.
    """

    def __init__(self, parent):
        super().__init__(parent)

        # 1. Create the Matplotlib Figure and Axes
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # 2. Create the Tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 3. Load the data and draw the plot
        self.load_and_plot_data()

    def load_and_plot_data(self):
        """
        Loads data from a specific CSV and generates a scatter plot.
        Includes error handling for missing files or columns.
        """
        filepath = r"PIMMS v1.2\import folder\big_mass_group.csv"

        try:
            # Attempt to load the data
            df = pd.read_csv(filepath)

            # Check for required columns
            required_cols = ["m/z", "CCS"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(
                    f"CSV is missing one or more required columns: {required_cols}"
                )

            # Clear any previous plot
            self.ax.clear()

            # Create the scatter plot
            self.ax.scatter(df["m/z"], df["CCS"], alpha=0.7)

            # Add labels and a title
            self.ax.set_title("m/z vs. CCS from big_mass_group.csv")
            self.ax.set_xlabel("m/z")
            self.ax.set_ylabel("CCS ($Å^2$)")
            self.ax.grid(True)

        except FileNotFoundError:
            self.display_error(
                f"Error: File not found.\nPlease ensure this file exists:\n{filepath}"
            )
        except Exception as e:
            self.display_error(f"An error occurred:\n{e}")

        # Ensure the plot is drawn, whether it's the data or an error message
        self.fig.tight_layout()
        self.canvas.draw()

    def display_error(self, message):
        """Displays an error message on the Matplotlib canvas."""
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            message,
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax.transAxes,
            fontsize=12,
            color="red",
            wrap=True,
            bbox=dict(boxstyle="round,pad=0.5", fc="ivory", alpha=0.9),
        )
        self.ax.set_title("Plotting Error")
        # Turn off axes for error messages
        self.ax.set_xticks([])
        self.ax.set_yticks([])
