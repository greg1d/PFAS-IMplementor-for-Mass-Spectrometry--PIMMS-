import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import webbrowser
import tempfile
import pandas as pd

try:
    from modules.isotopic_analysis import heavy_halogen_hunter
    from modules.Kaufman_plot_unintegrated import (
        calculate_and_classify_ratio,
        create_interactive_figure,
        run_full_pipeline,
    )
except ImportError:
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.isotopic_analysis import heavy_halogen_hunter
    from modules.Kaufman_plot_unintegrated import (
        create_interactive_figure,
        run_full_pipeline,
    )

TABLE_DISPLAY_CONFIG = {
    # Give columns user-friendly names for the table display
    "relabel": {
        "Match_ID": "Name",
        "Classification Type": "Class",
        "Isotopic_analysis": "Isotope Status",
        "Peak_mz_1": "m/z",
        "PIMMS_CCS": "CCS",
        "Predicted C/F ratio": "Pred. C/F Ratio",
        "Intensity_1": "Intensity",
    },
    # Defines the order of the main columns. Sample columns will be added after these.
    "order": [
        "Name",
        "Class",
        "Isotope Status",
        "m/z",
        "CCS",
        "Intensity",
        "Pred. C/F Ratio",
    ],
    # List of original column names to completely hide from the table view.
    "hide": [
        "AlignmentID",
        "Short_Match_ID",
        "M/M+2 Distribution",
        "Expected_M+2_Ratio_from_C",
        "Peak_mz_2",
        "Intensity_2",
        "Intensity_3",
        "mass_defect",
        "md_over_C",
        "Kaufman_C",
        "m_over_C",
        "DT",
        "RT",
        "Peak_mz",
        "Peak_intensity",
        "SourceFile",
    ],
    # Dictionary defining rounding rules for specific original column names.
    "round": {
        "Peak_mz_1": 4,
        "Intensity_1": 0,
        "PIMMS_CCS": 2,
    },
}


class IsotopicAnalysisTab(ttk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.pimms_filepath = tk.StringVar()
        self.cef_folder = tk.StringVar()
        self.results_df = None

        self._create_widgets()
        self._load_defaults()

    def _create_widgets(self):
        control_frame = ttk.Labelframe(self, text="Workflow", padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        control_frame.columnconfigure(1, weight=1)

        table_frame = ttk.Labelframe(self, text="Analysis Results", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Input Widgets ---
        ttk.Label(control_frame, text="PIMMS File:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(
            control_frame, textvariable=self.pimms_filepath, state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(
            control_frame, text="Browse...", command=self._select_pimms_file
        ).grid(row=0, column=2, padx=5)

        ttk.Label(control_frame, text="CEF Folder:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(control_frame, textvariable=self.cef_folder, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5
        )
        ttk.Button(
            control_frame, text="Browse...", command=self._select_cef_folder
        ).grid(row=1, column=2, padx=5)

        # --- Action Buttons ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        self.run_button = ttk.Button(
            action_frame,
            text="1. Run Full Pipeline & Analysis",
            command=self._run_pipeline_thread,
            state="disabled",
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        self.plot_button = ttk.Button(
            action_frame,
            text="2. Generate Kaufman Plot",
            command=self._launch_plot,
            state="disabled",
        )
        self.plot_button.pack(side=tk.LEFT, padx=5)

        # --- NEW: Add a 'Save' button ---
        self.save_button = ttk.Button(
            action_frame,
            text="3. Save Results...",
            command=self._save_results,
            state="disabled",
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        # --- End of New Code ---

        # --- Table Widget ---
        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def _load_defaults(self):
        # Your logic to load default paths from config can go here
        pass

    def _select_pimms_file(self):
        path = filedialog.askopenfilename(
            title="Select PIMMS CSV", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            self.pimms_filepath.set(path)
            self._check_inputs()

    def _select_cef_folder(self):
        path = filedialog.askdirectory(title="Select CEF Folder")
        if path:
            self.cef_folder.set(path)
            self._check_inputs()

    def _check_inputs(self):
        if self.pimms_filepath.get() and self.cef_folder.get():
            self.run_button.config(state="normal")
        else:
            self.run_button.config(state="disabled")

    def _run_pipeline_thread(self):
        self.run_button.config(state="disabled")
        self.plot_button.config(state="disabled")
        self.save_button.config(state="disabled")
        thread = threading.Thread(target=self._pipeline_target)
        thread.daemon = True
        thread.start()

    def _pipeline_target(self):
        try:

            def status_update(message):
                print(message)

            # Step 1: Run the full PIMMS-CEF pipeline to generate the summary table
            summary_table = run_full_pipeline(
                self.pimms_filepath.get(), self.cef_folder.get(), status_update
            )
            if summary_table is None or summary_table.empty:
                messagebox.showinfo(
                    "Complete", "Pipeline ran, but no matching features were found."
                )
                return

            # Step 2: Run heavy halogen analysis
            status_update("Running heavy halogen analysis...")
            analysis_df = heavy_halogen_hunter(summary_table)

            # Step 3: Calculate the Predicted C/F ratio
            status_update("Calculating Predicted C/F ratio...")
            grid_path = r"PIMMS v1.2\modules\kaufman_grid_data.npz"
            self.results_df = calculate_and_classify_ratio(analysis_df, grid_path)

            # Now, self.results_df contains ALL the data
            self._update_table(self.results_df)

            # Re-enable buttons on success
            self.plot_button.config(state="normal")
            self.save_button.config(state="normal")
            messagebox.showinfo(
                "Success", "Full analysis complete! Results are in the table."
            )
        except Exception as e:
            messagebox.showerror("Pipeline Error", f"An error occurred:\n{e}")
        finally:
            self.run_button.config(state="normal")

    # --- MODIFIED: This function is now much simpler ---
    def _launch_plot(self):
        if self.results_df is None or self.results_df.empty:
            return
        try:
            # The results_df is already fully processed, so we can use it directly
            fig = create_interactive_figure(
                self.results_df,
                r"PIMMS v1.2\modules\kaufman_contour_boundaries_SMOOTH.csv",
                r"PIMMS v1.2\modules\kaufman_grid_data.npz",
            )
            if fig:
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".html", encoding="utf-8"
                ) as f:
                    fig.write_html(f)
                    file_path = f.name
                webbrowser.open("file://" + os.path.realpath(file_path))
        except Exception as e:
            messagebox.showerror("Plotting Error", f"Failed to generate plot:\n{e}")

    def _format_df_for_display(self, df):
        """
        Applies rounding, formatting, reordering, and hiding of columns.
        Now dynamically rounds sample intensity columns.
        """
        df_display = df.copy()

        # 1. Apply rounding for specifically configured columns
        for col, decimals in TABLE_DISPLAY_CONFIG["round"].items():
            if col in df_display.columns:
                df_display[col] = pd.to_numeric(df_display[col], errors="coerce").round(
                    decimals
                )

        # 2. Identify all columns that are NOT samples
        non_sample_cols = set(TABLE_DISPLAY_CONFIG["hide"]) | set(
            TABLE_DISPLAY_CONFIG["relabel"].keys()
        )

        # 3. Identify sample columns by finding what's NOT in the non_sample_cols set
        sample_cols = sorted([col for col in df.columns if col not in non_sample_cols])

        # --- NEW: Dynamically apply integer rounding and formatting to all sample columns ---
        print(f"DEBUG: Formatting sample columns: {sample_cols}")
        for col in sample_cols:
            if col in df_display.columns:
                numeric_col = pd.to_numeric(df_display[col], errors="coerce")
                # Format as an integer with comma separators
                df_display[col] = numeric_col.apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else ""
                )
        # --- End of New Code ---

        # 4. Relabel the columns for a user-friendly display
        df_display.rename(columns=TABLE_DISPLAY_CONFIG["relabel"], inplace=True)

        # 5. Construct the final column order
        final_order = TABLE_DISPLAY_CONFIG["order"] + sample_cols

        # 6. Filter for only the columns that exist and are desired
        existing_cols_to_show = [
            col for col in final_order if col in df_display.columns
        ]

        return df_display[existing_cols_to_show]

    # --- NEW: Method to save the results to a user-chosen location ---
    def _save_results(self):
        if self.results_df is None:
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Results As",
            filetypes=[("CSV Files", "*.csv")],
            defaultextension=".csv",
            initialfile="analysis_results.csv",
        )
        if not save_path:
            return
        try:
            # The results_df is already fully processed, so we can save it directly
            self.results_df.to_csv(save_path, index=False)
            messagebox.showinfo(
                "Success",
                f"Results successfully saved to:\n{os.path.basename(save_path)}",
            )
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    # --- MODIFIED: This function now uses the formatter ---
    def _update_table(self, df):
        """
        Formats the DataFrame and then populates the Treeview.
        """
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            return

        # Apply the formatting rules before displaying
        df_for_display = self._format_df_for_display(df)

        self.tree["columns"] = list(df_for_display.columns)
        for col in df_for_display.columns:
            self.tree.heading(col, text=col, anchor=tk.W)  # Left-align headings
            self.tree.column(col, width=120, anchor=tk.W)  # Left-align data

        for index, row in df_for_display.iterrows():
            # Fill NaN values with an empty string for cleaner display
            self.tree.insert("", "end", values=[v if pd.notna(v) else "" for v in row])
