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

    def __init__(
        self, parent, config
    ):  # It needs the 'config' object from the main app
        super().__init__(parent)
        self.config = config
        self.experimental_filepath = None
        self.library_filepath = None
        self.full_results_df = None
        self._create_widgets()

    def _create_widgets(self):
        # --- Main Layout ---
        # The ControlsWidget handles all the buttons and entry fields
        self.controls = ControlsWidget(
            self,
            config=self.config,
            load_exp_callback=self._load_experimental_data,
            load_lib_callback=self._load_library_data,
            analyze_callback=self._run_pipeline,
        )
        self.controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        # A separate frame for the Trend Selector dropdown
        selector_frame = ttk.Labelframe(self, text="Trend Group Viewer")
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(selector_frame, text="Select Trend to View:").pack(
            side=tk.LEFT, padx=5, pady=5
        )
        self.trend_selector = ttk.Combobox(selector_frame, state="disabled", width=30)
        self.trend_selector.pack(side=tk.LEFT, padx=5, pady=5)
        self.trend_selector.bind("<<ComboboxSelected>>", self._on_trend_selected)

        # --- Paned Window for resizable Plot and Table ---
        plot_table_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        plot_table_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # The PlotWidget is the dedicated Matplotlib canvas
        self.plot = PlotWidget(plot_table_pane)
        plot_table_pane.add(self.plot, weight=3)

        # The Treeview is for displaying tabular data
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
        """Collects parameters and calls the main pipeline controller."""
        if not self.experimental_filepath or not self.library_filepath:
            messagebox.showwarning(
                "Missing Files", "Please select both an experimental and library file."
            )
            return
        repeating_units = self.controls.get_repeating_units()
        if repeating_units is None:
            return

        # In a real app, these would come from more GUI widgets in the ControlsWidget
        params = {
            "experimental_filepath": self.experimental_filepath,
            "library_filepath": self.library_filepath,
            "selected_repeating_units": repeating_units,
            "mass_error_ppm": 10,
            "min_valid_points": 3,
            "min_library_points": 0,
            "ransac_threshold": 4.0,
            "min_ransac_samples": 3,
        }

        try:
            self.update_idletasks()
            final_df = run_analysis_pipeline(**params)

            if final_df is not None and not final_df.empty:
                self.full_results_df = final_df
                self._populate_trend_selector()
                if self.trend_selector["values"]:
                    self.trend_selector.current(0)
                    self._on_trend_selected(None)
                messagebox.showinfo(
                    "Success",
                    "Analysis complete. Select a trend to view from the dropdown.",
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
        """Populates the trend selector Combobox with trend_group IDs."""
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
