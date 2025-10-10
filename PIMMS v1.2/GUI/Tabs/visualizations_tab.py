import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# This robustly imports your pipeline controller and modular widgets
try:
    from modules.visualization_analysis_pipeline import (
        run_analysis_pipeline,
        significant_figures_rounding,
    )

    from ..widgets.controls_widget import ControlsWidget
    from ..widgets.plot_widget import PlotWidget
except ImportError:
    # Fallback for different run environments
    import os
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.visualization_analysis_pipeline import (
        run_analysis_pipeline,
        significant_figures_rounding,
    )

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
        self._load_defaults()  # Auto-load files on startup

    def _create_widgets(self):
        # The ControlsWidget handles all the buttons and parameter inputs
        self.controls = ControlsWidget(
            self,
            config=self.config,
            load_exp_callback=self._load_experimental_data,
            load_lib_callback=self._load_library_data,
            analyze_callback=self._run_pipeline,
        )
        self.controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        # --- THIS IS THE CORRECT FRAME FOR THE DROPDOWN AND BUTTON ---
        selector_frame = ttk.Labelframe(self, text="Trend Group Viewer")
        selector_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(selector_frame, text="Select Trend to View:").pack(
            side=tk.LEFT, padx=5, pady=5
        )
        self.trend_selector = ttk.Combobox(selector_frame, state="disabled", width=30)
        # MODIFIED: Added expand=True, fill=tk.X to ensure button is pushed to the far right
        self.trend_selector.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
        self.trend_selector.bind("<<ComboboxSelected>>", self._on_trend_selected)

        # --- MOVED: The Export button is now created in the correct, visible frame ---
        self.export_button = ttk.Button(
            selector_frame,
            text="Export Full Results...",
            command=self._export_results,
            state="disabled",
        )
        self.export_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Paned Window for resizable Plot and Table ---
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

    def _export_results(self):
        """
        Opens a 'Save As' dialog and saves the full results DataFrame to a CSV file.
        """
        if self.full_results_df is None or self.full_results_df.empty:
            messagebox.showwarning(
                "No Data", "There are no analysis results to export."
            )
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Full Results As",
            filetypes=[("CSV Files", "*.csv")],
            defaultextension=".csv",
            initialfile="pfas_analysis_results.csv",  # Suggest a default filename
        )

        if not save_path:
            # User cancelled the dialog
            return

        try:
            # Use pandas to_csv to save the data; index=False avoids writing row numbers
            self.full_results_df.to_csv(save_path, index=False)
            messagebox.showinfo(
                "Success",
                f"Results successfully saved to:\n{os.path.basename(save_path)}",
            )
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save the file:\n\n{e}")

    def _load_defaults(self):
        """Checks the config object for default file paths and loads them."""
        print("[INFO] Checking for default files specified in config...")

        lib_path = self.config.library_filepath
        if lib_path and os.path.exists(lib_path):
            self.library_filepath = lib_path
            self.controls.set_lib_file_label(os.path.basename(lib_path))
            print(f"[INFO] Auto-loaded default library: {lib_path}")

        exp_path = self.config.experimental_filepath
        if exp_path and os.path.exists(exp_path):
            self.experimental_filepath = exp_path
            self.controls.set_exp_file_label(os.path.basename(exp_path))
            print(f"[INFO] Auto-loaded default experimental file: {exp_path}")

    def _load_experimental_data(self):
        path = filedialog.askopenfilename(
            title="Select Experimental Data File", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self.experimental_filepath = path
            self.controls.set_exp_file_label(os.path.basename(path))

    def _load_library_data(self):
        path = filedialog.askopenfilename(
            title="Select PFAS Library File", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self.library_filepath = path
            self.controls.set_lib_file_label(os.path.basename(path))

    def _run_pipeline(self):
        """Collects parameters from the GUI and calls the main pipeline controller."""
        if not self.experimental_filepath or not self.library_filepath:
            messagebox.showwarning(
                "Missing Files", "Please select both an experimental and library file."
            )
            return

        gui_params = self.controls.get_parameters()
        if gui_params is None:
            return

        # --- UPDATED: Create the full parameter dictionary for the pipeline ---
        pipeline_params = {
            "experimental_filepath": self.experimental_filepath,
            "library_filepath": self.library_filepath,
            # Analysis parameters from the controls
            "selected_repeating_units": gui_params["repeating_unit"],
            "mass_error_ppm": gui_params["mass_error_ppm"],
            "min_valid_points": gui_params["min_valid_points"],
            "min_library_points": gui_params["min_library_points"],
            "ransac_threshold_percentage": gui_params["trend_ccs_threshold_percentage"],
            "min_ransac_samples": 3,
            # Column mapping parameters from the controls
            "library_name_col_pos": gui_params["library_name_col_pos"],
            "library_mz_col_pos": gui_params["library_mz_col_pos"],
            "library_ccs_col_pos": gui_params["library_ccs_col_pos"],
            "library_rt_col_pos": gui_params["library_rt_col_pos"],
            "library_id_col_pos": gui_params["library_id_col_pos"],
            "exp_name_col_pos": gui_params["exp_name_col_pos"],
            "exp_mz_col_pos": gui_params["exp_mz_col_pos"],
            "exp_ccs_col_pos": gui_params["exp_ccs_col_pos"],
            "exp_rt_col_pos": gui_params["exp_rt_col_pos"],
            "exp_id_col_pos": gui_params["exp_id_col_pos"],
        }

        try:
            self.update_idletasks()
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
                self.full_results_df = None  # Clear previous results
                self._populate_trend_selector()
                self.plot.update_plot(None, None)
                self._update_table(None)
                messagebox.showinfo(
                    "Analysis Complete", "No valid trend groups were found."
                )
        except Exception as e:
            messagebox.showerror("Pipeline Error", f"A critical error occurred:\n\n{e}")
            # Also clear the UI in case of an error
            self.full_results_df = None
            self._populate_trend_selector()
            self.plot.update_plot(None, None)
            self._update_table(None)

    def _populate_trend_selector(self):
        """Populates the trend selector Combobox and manages result-dependent widgets."""

        # --- MODIFIED: Check for results once at the top ---
        has_results = (
            self.full_results_df is not None and not self.full_results_df.empty
        )

        if has_results:
            trend_ids = sorted(
                [g for g in self.full_results_df["trend_group"].unique() if g != -1]
            )
            self.trend_selector["values"] = trend_ids
            self.trend_selector.config(state="readonly" if trend_ids else "disabled")
        else:
            self.trend_selector["values"] = []
            self.trend_selector.set("")
            self.trend_selector.config(state="disabled")

        # --- NEW: Enable or disable the export button based on results ---
        self.export_button.config(state="normal" if has_results else "disabled")
        # --- End of New Code ---

    def _on_trend_selected(self, event):
        """Called when the user selects a new trend from the Combobox."""
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

    # --- METHOD TO UPDATE ---
    def _update_table(self, df):
        """
        Manages the data table (Treeview), rounding values for display.
        """
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return

        # --- NEW: Call the rounding function on the data before displaying it ---
        df_for_display = significant_figures_rounding(df)

        self.tree["columns"] = list(df_for_display.columns)
        for col in df_for_display.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        for index, row in df_for_display.iterrows():
            self.tree.insert("", "end", values=list(row.values))
