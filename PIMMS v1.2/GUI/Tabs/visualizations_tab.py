import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import your pipeline controller and modular widgets
from modules.visualization_analysis_pipeline import run_analysis_pipeline

from ..widgets.controls_widget import ControlsWidget
from ..widgets.plot_widget import PlotWidget


class VisualizationsTab(ttk.Frame):
    """
    The main tab for visualization, acting as a controller for interactive
    analysis and display of trend groups.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.experimental_filepath = None
        self.library_filepath = None
        self.full_results_df = None  # Will store the complete analysis result
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

        # Add the Trend Selector Combobox to the controls
        selector_frame = ttk.Labelframe(self.controls, text="Trend Group Viewer")
        selector_frame.pack(
            side=tk.LEFT, padx=10, pady=10, after=self.controls.file_frame
        )

        ttk.Label(selector_frame, text="Select Trend to View:").pack(pady=(5, 0))
        self.trend_selector = ttk.Combobox(selector_frame, state="disabled")
        self.trend_selector.pack(padx=5, pady=5)
        self.trend_selector.bind("<<ComboboxSelected>>", self._on_trend_selected)

        # --- Paned Window for Plot and Table ---
        plot_table_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        plot_table_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot = PlotWidget(plot_table_pane)
        plot_table_pane.add(self.plot, weight=3)

        table_frame = ttk.Labelframe(plot_table_pane, text="Selected Trend Data")
        plot_table_pane.add(table_frame, weight=1)

        self.tree = ttk.Treeview(table_frame, show="headings")
        # ... (Treeview and scrollbar setup is the same)
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
        """Collects parameters and calls the main pipeline controller."""
        if not self.experimental_filepath or not self.library_filepath:
            messagebox.showwarning("Missing Files", "Please select both files.")
            return
        repeating_units = self.controls.get_repeating_units()
        if repeating_units is None:
            return

        # Example parameters (in a real app, these would come from more GUI widgets)
        params = {
            "experimental_filepath": self.experimental_filepath,
            "library_filepath": self.library_filepath,
            "selected_repeating_units": repeating_units,
            "mass_error_ppm": 10,
            "min_valid_points": 4,
            "min_library_points": 1,
            "ransac_threshold": 4.0,
            "min_ransac_samples": 3,
        }

        try:
            # For a long process, use a thread
            final_df = run_analysis_pipeline(**params)

            if final_df is not None and not final_df.empty:
                self.full_results_df = final_df
                self._populate_trend_selector()
                self.trend_selector.current(0)
                self._on_trend_selected(None)  # Trigger display of the first trend
                messagebox.showinfo(
                    "Success",
                    "Analysis complete. Select a trend to view from the dropdown.",
                )
            else:
                self._populate_trend_selector()  # Clear dropdown
                self.plot.update_plot(None, None)  # Clear plot
                self._update_table(None)  # Clear table
                messagebox.showinfo(
                    "Analysis Complete", "No valid trend groups were found."
                )
        except Exception as e:
            messagebox.showerror("Pipeline Error", f"A critical error occurred: {e}")

    def _populate_trend_selector(self):
        """Populates the trend selector Combobox with trend_group IDs."""
        if self.full_results_df is not None and not self.full_results_df.empty:
            trend_ids = sorted(
                [g for g in self.full_results_df["trend_group"].unique() if g != -1]
            )
            self.trend_selector["values"] = trend_ids
            self.trend_selector.config(state="readonly")
        else:
            self.trend_selector["values"] = []
            self.trend_selector.set("")
            self.trend_selector.config(state="disabled")

    def _on_trend_selected(self, event):
        """Called when the user selects a new trend from the Combobox."""
        selected_trend_str = self.trend_selector.get()
        if not selected_trend_str or self.full_results_df is None:
            return

        selected_trend_id = float(selected_trend_str)

        # Filter data for the selected trend
        selected_trend_df = self.full_results_df[
            self.full_results_df["trend_group"] == selected_trend_id
        ]
        if selected_trend_df.empty:
            return

        # Get the parent GroupID for context
        parent_group_id = selected_trend_df["GroupID"].iloc[0]
        parent_group_df = self.full_results_df[
            self.full_results_df["GroupID"] == parent_group_id
        ]

        # Update UI
        self.plot.update_plot(parent_group_df, selected_trend_df)
        self._update_table(selected_trend_df)

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
