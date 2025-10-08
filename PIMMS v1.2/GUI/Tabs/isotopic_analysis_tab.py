import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import webview
import threading

# Import the newly organized analysis and plotting modules
try:
    from modules.isotopic_analysis import (
        heavy_halogen_hunter,
    )
    from modules.Kaufman_plot_unintegrated import (
        calculate_and_classify_ratio,
        create_interactive_figure,
    )
except ImportError:
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.isotopic_analysis import (
        heavy_halogen_hunter,
    )
    from modules.Kaufman_plot_unintegrated import (
        calculate_and_classify_ratio,
        create_interactive_figure,
    )


class IsotopicAnalysisTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.raw_data_df = None  # Holds the originally loaded data
        self.analysis_df = None  # Holds the data after isotopic analysis

        self._create_widgets()
        self._load_defaults()

    def _create_widgets(self):
        control_frame = ttk.Labelframe(self, text="Workflow", padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        table_frame = ttk.Labelframe(self, text="Isotopic Analysis Data", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Control Widgets ---
        self.load_button = ttk.Button(
            control_frame, text="1. Load Data File...", command=self._load_data_file
        )
        self.load_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.analyze_button = ttk.Button(
            control_frame,
            text="2. Run Isotopic Analysis",
            command=self._run_analysis,
            state="disabled",
        )
        self.analyze_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.plot_button = ttk.Button(
            control_frame,
            text="3. Generate Kaufman Plot",
            command=self._launch_plot,
            state="disabled",
        )
        self.plot_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.file_label = ttk.Label(
            control_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        # --- Table Widget ---
        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_defaults(self):
        # Using a general path from your main config object
        if hasattr(self.config, "output_filepath") and self.config.output_filepath:
            default_path = self.config.output_filepath
            if default_path and os.path.exists(default_path):
                self._load_file(default_path)

    def _load_data_file(self):
        path = filedialog.askopenfilename(
            title="Select Data Table", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path):
        self.filepath = path
        self.file_label.config(text=os.path.basename(path))
        try:
            self.raw_data_df = pd.read_csv(path)
            self._update_table(self.raw_data_df)
            self.analyze_button.config(state="normal")
            self.plot_button.config(
                state="disabled"
            )  # Disable plot until analysis is run
            messagebox.showinfo(
                "Success", f"Loaded {len(self.raw_data_df)} rows. Ready for analysis."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.raw_data_df = None
            self.analyze_button.config(state="disabled")

    def _run_analysis(self):
        if self.raw_data_df is None:
            return
        try:
            print("Running isotopic analysis...")
            self.analysis_df = heavy_halogen_hunter(self.raw_data_df)
            self._update_table(self.analysis_df)
            self.plot_button.config(state="normal")
            messagebox.showinfo("Success", "Isotopic analysis complete.")
        except Exception as e:
            messagebox.showerror(
                "Analysis Error", f"An error occurred during analysis:\n{e}"
            )

    def _launch_plot(self):
        if self.analysis_df is None:
            return

        # Define required file paths for plotting overlays
        contour_boundary_path = (
            r"PIMMS v1.2\modules\kaufman_contour_boundaries_SMOOTH.csv"
        )
        grid_data_path = r"PIMMS v1.2\modules\kaufman_grid_data.npz"
        print("loaded data", self.analysis_df.head())
        try:
            # Add the 'Predicted C/F ratio' column for plotting and export
            df_to_plot = calculate_and_classify_ratio(self.analysis_df, grid_data_path)

            if df_to_plot is None:
                return
            print("data about to be plotted", df_to_plot.head())

            # Create the interactive figure
            fig = create_interactive_figure(
                df_to_plot, contour_boundary_path, grid_data_path
            )

            if fig:
                # This helper runs webview in a separate thread so the main GUI doesn't freeze
                def run_webview():
                    html_content = fig.to_html(include_plotlyjs="cdn")
                    webview.create_window(
                        "Interactive Kaufman Plot",
                        html=html_content,
                        width=900,
                        height=700,
                    )
                    webview.start()

                thread = threading.Thread(target=run_webview)
                thread.daemon = True
                thread.start()

        except Exception as e:
            messagebox.showerror("Plotting Error", f"Failed to generate plot:\n{e}")

    def _update_table(self, df):
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row.values))
