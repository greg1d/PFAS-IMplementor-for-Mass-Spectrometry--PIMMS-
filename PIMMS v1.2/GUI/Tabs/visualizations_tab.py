import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from modules.visualization_analysis_pipeline import run_analysis_pipeline

from ..widgets.controls_widget import ControlsWidget
from ..widgets.plot_widget import PlotWidget


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
        self.controls = ControlsWidget(
            self,
            self._load_experimental_data,
            self._load_library_data,
            self._run_pipeline,
        )
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

    def _load_experimental_data(self):
        path = filedialog.askopenfilename(
            title="Select Experimental Data File (adjusted_df)",
            filetypes=[("CSV Files", "*.csv")],
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
            self.controls.set_lib_file_label("Lib: " + path.split("/")[-1])

    def _run_pipeline(self):
        """Collects parameters and calls the main pipeline controller."""
        # 1. Validate inputs
        if not self.experimental_filepath or not self.library_filepath:
            messagebox.showwarning(
                "Missing Files",
                "Please select both an experimental data file and a library file.",
            )
            return

        repeating_units = self.controls.get_repeating_units()
        if repeating_units is None:
            return

        # 2. Collect all parameters from the GUI (here we use examples, you would get from entry boxes)
        params = {
            "experimental_filepath": self.experimental_filepath,
            "library_filepath": self.library_filepath,
            "selected_repeating_units": repeating_units,
            "mass_error_ppm": 10,  # Example: get from a ttk.Entry
            "min_valid_points": 4,  # Example
            "min_library_points": 1,  # Example
            "ransac_threshold": 4.0,  # Example
            "min_ransac_samples": 3,  # Example
        }

        # 3. Run the pipeline
        try:
            # This is where you would normally use a thread to prevent freezing
            # For simplicity here, we run it directly.
            self.update_idletasks()  # Ensure GUI is responsive before starting

            final_df = run_analysis_pipeline(**params)

            # 4. Update UI with results
            if final_df is not None:
                self.plot.update_plot(
                    None, final_df
                )  # We only need to plot the final trends
                self._update_table(final_df)
                messagebox.showinfo(
                    "Success", "Analysis pipeline completed successfully."
                )
            else:
                messagebox.showerror(
                    "Error", "Analysis pipeline failed. Check the console for details."
                )

        except Exception as e:
            messagebox.showerror("Pipeline Error", f"A critical error occurred: {e}")

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
