import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# This robustly imports your analysis function from the 'modules' directory
try:
    from modules.ccsvmz_analysis import mz_group_refinement, mz_repeating_unit_analysis
except ImportError:
    import os
    import sys

    # Navigate up two levels from GUI/Tabs to the project root 'PIMMS v1.2'
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # Now that the path is set, try importing again
    from modules.ccsvmz_analysis import mz_repeating_unit_analysis


class VisualizationsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.raw_df = None  # This will hold the loaded data
        self._create_widgets()

    def _create_widgets(self):
        # --- Main Layout Panes for resizable sections ---
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.Labelframe(main_pane, text="Controls")
        plot_table_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(controls_frame, weight=0)
        main_pane.add(plot_table_pane, weight=1)

        plot_frame = ttk.Frame(plot_table_pane)
        table_frame = ttk.Labelframe(plot_table_pane, text="Data Table")
        plot_table_pane.add(plot_frame, weight=3)
        plot_table_pane.add(table_frame, weight=1)

        # --- Control Widgets ---
        self.load_btn = ttk.Button(
            controls_frame, text="Load Report File...", command=self._load_data
        )  # <-- FIX #1: Added command
        self.load_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.file_label = ttk.Label(controls_frame, text="No file loaded.")
        self.file_label.pack(side=tk.LEFT, padx=10, pady=10)

        analysis_frame = ttk.Frame(controls_frame)
        analysis_frame.pack(side=tk.LEFT, padx=20, pady=5, fill=tk.X, expand=True)

        ttk.Label(analysis_frame, text="Repeating Unit (e.g., CF2:49.9968):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.unit_entry = ttk.Entry(analysis_frame, width=20)
        self.unit_entry.insert(0, "CF2:49.9968")
        self.unit_entry.grid(row=0, column=1, padx=5, pady=5)

        self.reanalyze_btn = ttk.Button(
            analysis_frame,
            text="Find Trends & Plot",
            state="disabled",
            command=self._analyze_and_plot,
        )
        self.reanalyze_btn.grid(row=0, column=2, padx=10, pady=5)

        # --- Matplotlib Plot Canvas ---
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._update_plot(None)  # Initial drawing

        # --- Data Table (Treeview) ---
        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_data(self):
        """Opens a file dialog to load a CSV report file."""
        path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            self.raw_df = pd.read_csv(path)
            self.file_label.config(text=path.split("/")[-1])
            self.reanalyze_btn.config(state="normal")

            self._update_table(self.raw_df)

            # Clear the plot and show a ready message
            self.ax.clear()
            self.ax.text(
                0.5,
                0.5,
                "Data loaded. Click 'Find Trends & Plot' to analyze.",
                ha="center",
                va="center",
                transform=self.ax.transAxes,  # Use axis coordinates
            )
            # Redraw title and grid for consistency
            self.ax.set_title("CCS vs. m/z Homologous Series")
            self.ax.grid(True)
            self.canvas.draw()

            messagebox.showinfo("Success", f"Loaded {len(self.raw_df)} records.")
        except Exception as e:
            messagebox.showerror(
                "Error Loading File", f"Could not read the file.\nError: {e}"
            )
            self.raw_df = None

    def _update_table(self, df):
        """Clears and repopulates the data table."""
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        # <-- FIX #2: Correctly get values from the row for insertion
        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row.values))

    def _parse_repeating_units(self):
        """Parses the text from the entry box into a dictionary."""
        try:
            text = self.unit_entry.get()
            if not text:
                return {}
            name, mass = text.split(":")
            return {name.strip(): float(mass)}
        except Exception:
            messagebox.showerror(
                "Invalid Format",
                "Repeating unit must be 'Name:Mass' (e.g., 'CF2:49.9968').",
            )
            return None

    def _analyze_and_plot(self):
        """Runs the analysis logic on the loaded data and updates the UI."""
        if self.raw_df is None:
            messagebox.showwarning("No Data", "Please load a data file first.")
            return

        repeating_units = self._parse_repeating_units()
        if repeating_units is None:
            return

        try:
            print("Finding homologous series...")
            analyzed_df = mz_repeating_unit_analysis(
                self.raw_df.copy(), repeating_units
            )
            print("Analysis complete.")
            self._update_plot(analyzed_df)
            self._update_table(analyzed_df if not analyzed_df.empty else self.raw_df)
        except Exception as e:
            messagebox.showerror(
                "Analysis Error", f"An error occurred during analysis:\n{e}"
            )

    def _update_plot(self, analyzed_df):
        """Clears and redraws the Matplotlib plot."""
        self.ax.clear()

        # Plot all original points as a gray background for context
        if self.raw_df is not None:
            self.ax.scatter(
                self.raw_df["m/z"],
                self.raw_df["CCS"],
                color="gray",
                alpha=0.2,
                label="All Features",
            )

        if analyzed_df is None or analyzed_df.empty:
            if self.raw_df is not None:  # If data is loaded but no groups found
                self.ax.text(
                    0.5,
                    0.5,
                    "No homologous series found for these parameters.",
                    ha="center",
                    va="center",
                    transform=self.ax.transAxes,
                )
            else:  # Before any data is loaded
                self.ax.text(
                    0.5,
                    0.5,
                    "Load a report file to begin.",
                    ha="center",
                    va="center",
                    transform=self.ax.transAxes,
                )
        else:
            # Plot each homologous series group in a different color
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
