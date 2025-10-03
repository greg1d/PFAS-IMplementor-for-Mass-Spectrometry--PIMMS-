import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import your pipeline controller and modular widgets
try:
    from modules.visualization_analysis_pipeline import run_analysis_pipeline

    from ..widgets.controls_widget import ControlsWidget
    from ..widgets.plot_widget import PlotWidget
except ImportError:
    # Fallback for running file directly or path issues
    import os
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.visualization_analysis_pipeline import run_analysis_pipeline

    from GUI.widgets.controls_widget import ControlsWidget
    from GUI.widgets.plot_widget import PlotWidget


class VisualizationsTab(ttk.Frame):
    """
    The main tab for visualization, acting as a controller for interactive
    analysis and display of trend groups.
    """

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.experimental_filepath = None
        self.library_filepath = None
        self.full_results_df = None
        self._create_widgets()

    def _create_widgets(self):
        # --- Main Layout ---
        self.controls = ControlsWidget(
            self,
            config=self.config,
            load_exp_callback=self._load_experimental_data,
            load_lib_callback=self._load_library_data,
            analyze_callback=self._run_pipeline,
        )
        self.controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        selector_frame = ttk.Labelframe(self, text="Trend Group Viewer")
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(selector_frame, text="Select Trend to View:").pack(
            side=tk.LEFT, padx=5, pady=5
        )
        self.trend_selector = ttk.Combobox(selector_frame, state="disabled", width=30)
        self.trend_selector.pack(side=tk.LEFT, padx=5, pady=5)
        self.trend_selector.bind("<<ComboboxSelected>>", self._on_trend_selected)

        plot_table_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        plot_table_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot = PlotWidget(plot_table_pane)
        plot_table_pane.add(self.plot, weight=3)

        table_frame = ttk.Labelframe(plot_table_pane, text="Selected Trend Data")
        plot_table_pane.add(table_frame, weight=1)
        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_experimental_data(self):
        path = filedialog.askopenfilename(
            title="Select Experimental Data File", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self.experimental_filepath = path
            self.controls.set_exp_file_label(path.split("/")[-1])

    def _load_library_data(self):
        path = filedialog.askopenfilename(
            title="Select PFAS Library File", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self.library_filepath = path
            self.controls.set_lib_file_label(path.split("/")[-1])

    def _run_pipeline(self):
        """Collects parameters from the GUI and calls the main pipeline controller."""
        if not self.experimental_filepath or not self.library_filepath:
            messagebox.showwarning(
                "Missing Files", "Please select both an experimental and library file."
            )
            return

        # --- MODIFICATION: Get all parameters from the ControlsWidget ---
        gui_params = self.controls.get_parameters()
        if gui_params is None:
            return  # An error occurred in parameter parsing (e.g., invalid number)

        # Create the full parameter dictionary for the pipeline
        pipeline_params = {
            "experimental_filepath": self.experimental_filepath,
            "library_filepath": self.library_filepath,
            "selected_repeating_units": gui_params["repeating_unit"],
            "mass_error_ppm": gui_params["mass_error_ppm"],
            "min_valid_points": gui_params["min_valid_points"],
            "min_library_points": gui_params["min_library_points"],
            "ransac_threshold_percentage": gui_params["ransac_threshold_percentage"],
            "min_ransac_samples": 3,  # This can also be made into a GUI control if needed
        }
        # --- END MODIFICATION ---

        try:
            self.update_idletasks()
            # Run the pipeline with the parameters collected from the GUI
            final_df = run_analysis_pipeline(**pipeline_params)

            if final_df is not None and not final_df.empty:
                self.full_results_df = final_df
                self._populate_trend_selector()
                if self.trend_selector["values"]:
                    self.trend_selector.current(0)
                    self._on_trend_selected(None)
                messagebox.showinfo(
                    "Success", "Analysis complete. Select a trend to view."
                )
            else:
                self._populate_trend_selector()
                self.plot.update_plot(None, None)
                self._update_table(None)
                messagebox.showinfo(
                    "Analysis Complete", "No valid trend groups were found."
                )
        except Exception as e:
            messagebox.showerror("Pipeline Error", f"A critical error occurred: {e}")

    def _populate_trend_selector(self):
        if self.full_results_df is not None and not self.full_results_df.empty:
            trend_ids = sorted(
                [g for g in self.full_results_df["trend_group"].unique() if g != -1]
            )
            self.trend_selector["values"] = trend_ids
            self.trend_selector.config(state="readonly" if trend_ids else "disabled")
        else:
            self.trend_selector["values"] = []
            self.trend_selector.set("")
            self.trend_selector.config(state="disabled")

    def _on_trend_selected(self, event):
        selected_trend_str = self.trend_selector.get()
        if not selected_trend_str or self.full_results_df is None:
            return
        selected_trend_id = float(selected_trend_str)
        selected_trend_df = self.full_results_df[
            self.full_results_df["trend_group"] == selected_trend_id
        ]
        if selected_trend_df.empty:
            return
        parent_group_id = selected_trend_df["GroupID"].iloc[0]
        parent_group_df = self.full_results_df[
            self.full_results_df["GroupID"] == parent_group_id
        ]
        self.plot.update_plot(parent_group_df, selected_trend_df)
        self._update_table(selected_trend_df)

    def _update_table(self, df):
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row.values))
