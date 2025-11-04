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
        Clears and redraws the plot, overlays (x, y) coordinates above each point,
        avoiding overlaps, with black text and colored background. Vertical offset
        is a percentage of the y-axis range.
        """
        self.ax.clear()
        label_positions = []  # Keep track of previously drawn label positions
        min_dist = 5  # Minimum distance between labels in data units
        offset_pct = 0.06  # 6% of y-axis range

        def can_place_label(x, y):
            for lx, ly in label_positions:
                if abs(x - lx) < min_dist and abs(y - ly) < min_dist:
                    return False
            label_positions.append((x, y))
            return True

        def draw_label(x, y, text):
            ylim = self.ax.get_ylim()
            y_offset = (ylim[1] - ylim[0]) * offset_pct  # dynamic offset
            if can_place_label(x, y):
                self.ax.text(
                    x,
                    y + y_offset,
                    text,
                    fontsize=7,
                    ha="center",
                    va="bottom",
                    color="black",
                    bbox=dict(facecolor="#4B9CD3", alpha=0.8, edgecolor="none", pad=1),
                )

        # -------- Plot parent group (gray) --------
        if context_df is not None and not context_df.empty:
            gray_df = context_df.copy()

            # Exclude External Standards that are highlighted
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
                    zorder=1,
                )
                for idx, row in gray_df.iterrows():
                    draw_label(
                        row["m/z"], row["CCS"], f"({row['m/z']:.2f}, {row['CCS']:.2f})"
                    )

                # -------- Plot highlighted points (colored by Classification Type) --------# -------- Plot highlighted points --------
        if highlighted_df is not None and not highlighted_df.empty:
            trend_id = highlighted_df["GroupID"].iloc[0]

            # Assign colors based on 'is_outlier' column
            def get_point_color(row):
                return "#2F07AF" if row.get("is_outlier", False) else "#EB8002"

            # Split data by Classification Type
            standards_df = highlighted_df[
                highlighted_df["Classification Type"] == "External Standard"
            ]
            other_points_df = highlighted_df[
                highlighted_df["Classification Type"] != "External Standard"
            ]

            # Plot other points (non-standards) with color based on outlier status
            if not other_points_df.empty:
                colors = other_points_df.apply(get_point_color, axis=1)
                self.ax.scatter(
                    other_points_df["m/z"],
                    other_points_df["CCS"],
                    marker="o",
                    color=colors,
                    s=50,
                    label="Sample Feature",
                    zorder=5,
                )
                for idx, row in other_points_df.iterrows():
                    draw_label(
                        row["m/z"], row["CCS"], f"({row['m/z']:.2f}, {row['CCS']:.2f})"
                    )

            # Standards as green X
            if not standards_df.empty:
                colors = standards_df.apply(get_point_color, axis=1)
                self.ax.scatter(
                    standards_df["m/z"],
                    standards_df["CCS"],
                    marker="x",
                    color=colors,
                    s=80,
                    label="External Standard",
                    zorder=10,
                )
                for idx, row in standards_df.iterrows():
                    draw_label(
                        row["m/z"], row["CCS"], f"({row['m/z']:.2f}, {row['CCS']:.2f})"
                    )

            # Fit trend line (only with non-outlier points)
            trend_df = highlighted_df[highlighted_df["is_outlier"] == False]
            if not trend_df.empty and len(trend_df) >= 2:
                model = LinearRegression().fit(
                    trend_df[["m/z"]].values, trend_df["CCS"].values
                )
                x_range = np.linspace(trend_df["m/z"].min(), trend_df["m/z"].max(), 100)
                y_pred = model.predict(x_range.reshape(-1, 1))
                self.ax.plot(
                    x_range,
                    y_pred,
                    linestyle="--",
                    color="black",
                    label=f"Trend {trend_id} Fit",
                    zorder=0,
                )
            else:
                print(
                    f"[INFO] Trend {trend_id} has insufficient non-outlier points for line fit."
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

        # ----- Consistent legend -----
        from matplotlib.lines import Line2D

        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="#2F07AF",
                markeredgecolor="none",
                label="Outlier (Sample)",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="#F17105",
                markeredgecolor="none",
                label="Inlier (Sample)",
            ),
            Line2D(
                [0],
                [0],
                marker="x",
                color="#2F07AF",
                markersize=8,
                linestyle="none",
                label="Outlier (Library)",
            ),
            Line2D(
                [0],
                [0],
                marker="x",
                color="#F17105",
                markersize=8,
                linestyle="none",
                label="Inlier (Library)",
            ),
            Line2D([0], [0], linestyle="--", color="black", label="Trend Fit"),
        ]

        self.ax.legend(handles=legend_elements, loc="best")

        self.fig.tight_layout()
        self.canvas.draw()
