import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from ..widgets.controls_widget import ControlsWidget
from ..widgets.plot_widget import PlotWidget

# Import your analysis functions
try:
    from modules.ccsvmz_analysis import mz_repeating_unit_analysis
except ImportError:
    import os
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.ccsvmz_analysis import mz_repeating_unit_analysis


class VisualizationsTab(ttk.Frame):
    """
    The main tab for visualization, which acts as a controller for the
    controls, plot, and table widgets.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.raw_df = None
        self._create_widgets()

    def _create_widgets(self):
        # --- Main Layout ---
        self.controls = ControlsWidget(self, self._load_data, self._analyze_and_plot)
        self.controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        plot_table_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        plot_table_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot = PlotWidget(plot_table_pane)
        plot_table_pane.add(self.plot, weight=3)

        table_frame = ttk.Labelframe(plot_table_pane, text="Data Table")
        plot_table_pane.add(table_frame, weight=1)

        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_data(self):
        """Callback for the 'Load' button in the ControlsWidget."""
        path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.raw_df = pd.read_csv(path)
            # Communicate with the controls widget to update its state
            self.controls.set_file_label(path.split("/")[-1])
            self.controls.set_analyze_button_state("normal")

            # Update the UI
            self._update_table(self.raw_df)
            self.plot.update_plot(self.raw_df, None)
            messagebox.showinfo("Success", f"Loaded {len(self.raw_df)} records.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            self.raw_df = None

    def _analyze_and_plot(self):
        """Callback for the 'Find Trends' button in the ControlsWidget."""
        if self.raw_df is None:
            messagebox.showwarning("No Data", "Please load a data file first.")
            return

        repeating_units = self.controls.get_repeating_units()
        if repeating_units is None:
            return

        try:
            print("Finding homologous series...")
            analyzed_df = mz_repeating_unit_analysis(
                self.raw_df.copy(), repeating_units
            )
            print("Analysis complete.")

            # Pass data to the plot and table widgets
            self.plot.update_plot(self.raw_df, analyzed_df)
            self._update_table(analyzed_df if not analyzed_df.empty else self.raw_df)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred: {e}")

    def _update_table(self, df):
        """Manages the data table (Treeview)."""
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row.values))
