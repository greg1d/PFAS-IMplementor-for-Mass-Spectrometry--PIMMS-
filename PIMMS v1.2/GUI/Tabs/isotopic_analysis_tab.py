import os
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

import pandas as pd

try:
    from modules.isotopic_analysis import heavy_halogen_hunter
    from modules.Kaufman_plot_unintegrated import (
        calculate_and_classify_ratio,
        create_interactive_figure,
        run_full_pipeline,
    )

    from ..utils import resource_path
    from ..widgets.scrollable_table_widget import ScrollableTable
    from ..widgets.tooltip import Tooltip
except ImportError:
    import sys

    from GUI.widgets.tooltip import Tooltip

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
        "Predicted C/F ratio": "Pred. F/C Ratio",
        "Intensity_1": "Average Abundance",
        "DT_PIMMS": "DT",
        "RT_PIMMS": "RT",
    },
    # Defines the order of the main columns. Sample columns will be added after these.
    "order": [
        "Name",
        "Class",
        "Isotope Status",
        "m/z",
        "CCS",
        "DT",
        "RT",
        "Average Abundance",
        "Pred. F/C Ratio",
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
        "Peak_mz",
        "Peak_intensity",
        "SourceFile",
    ],
    # Dictionary defining rounding rules for specific original column names.
    "round": {
        "Peak_mz_1": 4,
        "Intensity_1": 0,
        "PIMMS_CCS": 2,
        "DT_PIMMS": 2,
        "RT_PIMMS": 2,
    },
}


class IsotopicAnalysisTab(ttk.Frame):
    def __init__(self, parent, config):
        print("[DEBUG] IsotopicAnalysisTab initializing...")
        super().__init__(parent)
        self.config = config
        self.pimms_filepath = tk.StringVar()
        self.cef_folder = tk.StringVar()
        self.results_df = None

        self._create_widgets()
        self._load_defaults()
        print("[DEBUG] IsotopicAnalysisTab initialization complete.")

    def _create_widgets(self):
        # --- Define all help texts in one place for easy editing ---
        help_texts = {
            "pimms_file": "Select the primary input CSV file from the PIMMS processing pipeline. This file should contain the list of all detected features.",
            "cef_folder": "Select any single .cef file from the folder containing all raw data files. The application will automatically use the folder path to find the necessary raw data for isotopic analysis.",
            "run_pipeline": "1. Processes the PIMMS file to find potential halogenated compounds.\n2. Extracts isotopic profiles from the raw .cef files.\n3. Performs heavy halogen analysis.\n4. Calculates Kaufmann plot parameters.\n\nThis can take several minutes to complete.",
            "launch_plot": "Generates and opens an interactive Kaufmann plot in your web browser. This button is enabled only after the main pipeline has been run successfully.",
            "save_results": "Saves the full data table, including all calculated values, to a CSV file. This button is enabled only after the main pipeline has been run successfully.",
            "results_table": "Displays the final results after the analysis is complete, showing key metrics and classification for each identified feature.",
        }

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

        help_pimms = ttk.Label(control_frame, text=" (?) ", cursor="question_arrow")
        help_pimms.grid(row=0, column=3, sticky="w")
        Tooltip(help_pimms, text=help_texts["pimms_file"])

        ttk.Label(control_frame, text="CEF Folder:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(control_frame, textvariable=self.cef_folder, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=5
        )
        ttk.Button(
            control_frame, text="Browse...", command=self._select_cef_folder
        ).grid(row=1, column=2, padx=5)

        help_cef = ttk.Label(control_frame, text=" (?) ", cursor="question_arrow")
        help_cef.grid(row=1, column=3, sticky="w")
        Tooltip(help_cef, text=help_texts["cef_folder"])

        # --- Action Buttons ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.run_button = ttk.Button(
            action_frame,
            text="1. Run Full Pipeline & Analysis",
            command=self._run_pipeline_thread,
            state="disabled",
        )
        self.run_button.grid(row=0, column=0, padx=(0, 2))

        help_run = ttk.Label(action_frame, text=" (?) ", cursor="question_arrow")
        help_run.grid(row=0, column=1, padx=(0, 10))
        Tooltip(help_run, text=help_texts["run_pipeline"])

        self.plot_button = ttk.Button(
            action_frame,
            text="2. Generate Kaufmann Plot",
            command=self._launch_plot,
            state="disabled",
        )
        self.plot_button.grid(row=0, column=2, padx=(0, 2))

        help_plot = ttk.Label(action_frame, text=" (?) ", cursor="question_arrow")
        help_plot.grid(row=0, column=3, padx=(0, 10))
        Tooltip(help_plot, text=help_texts["launch_plot"])

        self.save_button = ttk.Button(
            action_frame,
            text="3. Save Results...",
            command=self._save_results,
            state="disabled",
        )
        self.save_button.grid(row=0, column=4, padx=(0, 2))

        help_save = ttk.Label(action_frame, text=" (?) ", cursor="question_arrow")
        help_save.grid(row=0, column=5, padx=(0, 10))
        Tooltip(help_save, text=help_texts["save_results"])

        # --- Results Table ---
        self.table = ScrollableTable(table_frame)
        self.table.pack(fill="both", expand=True)

        help_table = ttk.Label(table_frame, text=" (?) ", cursor="question_arrow")
        help_table.place(relx=1.0, rely=0.0, x=-5, y=-8, anchor="ne")
        Tooltip(help_table, text=help_texts["results_table"])

    def _load_defaults(self):
        # Your logic to load default paths from config can go here
        pass

    def _select_pimms_file(self):
        print("[DEBUG] Selecting PIMMS file...")
        path = filedialog.askopenfilename(
            title="Select PIMMS CSV", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            print(f"[DEBUG] PIMMS file selected: {path}")
            self.pimms_filepath.set(path)
            self._check_inputs()

    def _select_cef_folder(self):
        print("[DEBUG] Selecting CEF folder...")
        # --- MODIFIED: Use askdirectory to select a folder directly ---
        folder_path = filedialog.askdirectory(title="Select CEF Data Folder")

        if folder_path:
            print(f"[DEBUG] CEF folder selected: {folder_path}")
            self.cef_folder.set(folder_path)
            self._check_inputs()
        # --- End of Modification ---

    def _check_inputs(self):
        if self.pimms_filepath.get() and self.cef_folder.get():
            self.run_button.config(state="normal")
            print("[DEBUG] Inputs valid. Run button enabled.")
        else:
            self.run_button.config(state="disabled")

    def _run_pipeline_thread(self):
        print("[DEBUG] Starting pipeline thread...")
        self.run_button.config(state="disabled")
        self.plot_button.config(state="disabled")
        self.save_button.config(state="disabled")
        thread = threading.Thread(target=self._pipeline_target)
        thread.daemon = True
        thread.start()

    def _pipeline_target(self):
        print("[DEBUG] Inside pipeline thread.")
        try:

            def status_update(message):
                print(f"[PIPELINE STATUS] {message}")

            # Step 1: Run the full PIMMS-CEF pipeline
            print("[DEBUG] Calling run_full_pipeline...")
            summary_table = run_full_pipeline(
                self.pimms_filepath.get(), self.cef_folder.get(), status_update
            )

            if summary_table is None:
                print("[DEBUG] run_full_pipeline returned None.")
            elif summary_table.empty:
                print("[DEBUG] run_full_pipeline returned EMPTY DataFrame.")
            else:
                print(
                    f"[DEBUG] run_full_pipeline returned DataFrame with shape: {summary_table.shape}"
                )

            if summary_table is None or summary_table.empty:
                messagebox.showinfo(
                    "Complete", "Pipeline ran, but no matching features were found."
                )
                return

            # Step 2: Run heavy halogen analysis
            status_update("Running heavy halogen analysis...")
            print("[DEBUG] Calling heavy_halogen_hunter...")
            analysis_df = heavy_halogen_hunter(summary_table)
            print(f"[DEBUG] heavy_halogen_hunter complete. Shape: {analysis_df.shape}")

            # Step 3: Calculate the Predicted C/F ratio
            status_update("Calculating Predicted C/F ratio...")
            grid_path = resource_path("modules/kaufman_grid_data.npz")
            print(f"[DEBUG] Loading grid data from: {grid_path}")

            self.results_df = calculate_and_classify_ratio(analysis_df, grid_path)

            if self.results_df is not None:
                print(
                    f"[DEBUG] Ratio classification complete. Results DF shape: {self.results_df.shape}"
                )

                # Check column existence
                if "Predicted C/F ratio" in self.results_df.columns:
                    print("[DEBUG] 'Predicted C/F ratio' column present.")
                else:
                    print("[DEBUG] ERROR: 'Predicted C/F ratio' column MISSING.")

                # Now, self.results_df contains ALL the data
                self._update_table(self.results_df)

                # Re-enable buttons on success
                self.plot_button.config(state="normal")
                self.save_button.config(state="normal")
                messagebox.showinfo(
                    "Success", "Full analysis complete! Results are in the table."
                )
            else:
                print("[DEBUG] calculate_and_classify_ratio returned None.")
                messagebox.showerror("Error", "Ratio calculation failed (check logs).")

        except Exception as e:
            print(f"[DEBUG] Pipeline Exception: {e}")
            import traceback

            traceback.print_exc()
            messagebox.showerror("Pipeline Error", f"An error occurred:\n{e}")
        finally:
            self.run_button.config(state="normal")
            print("[DEBUG] Pipeline thread exiting.")

    def _launch_plot(self):
        print("[DEBUG] _launch_plot called.")
        if self.results_df is None or self.results_df.empty:
            print("[DEBUG] No results to plot.")
            return
        try:
            print("[DEBUG] Generating interactive figure...")
            fig = create_interactive_figure(
                self.results_df,
                resource_path("modules/kaufman_contour_boundaries_SMOOTH.csv"),
                resource_path("modules/kaufman_grid_data.npz"),
            )
            if fig:
                print("[DEBUG] Figure created. Saving to temp file...")
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".html", encoding="utf-8"
                ) as f:
                    fig.write_html(f)
                    file_path = f.name

                print(f"[DEBUG] Opening browser: {file_path}")
                webbrowser.open("file://" + os.path.realpath(file_path))
            else:
                print("[DEBUG] create_interactive_figure returned None.")
        except Exception as e:
            print(f"[DEBUG] Plotting Exception: {e}")
            messagebox.showerror("Plotting Error", f"Failed to generate plot:\n{e}")

    def _format_df_for_display(self, df):
        """
        Applies rounding, formatting, reordering, and hiding of columns.
        Now dynamically rounds sample intensity columns.
        """
        print(f"[DEBUG] _format_df_for_display called. Input shape: {df.shape}")
        df_display = df.copy()
        max_len = 35

        if "Match_ID" in df_display.columns:
            df_display["Match_ID"] = (
                df_display["Match_ID"]
                .astype(str)
                .apply(lambda x: (x[: max_len - 3] + "...") if len(x) > max_len else x)
            )

        # 1. Apply rounding for specifically configured columns
        print("[DEBUG] Applying specific column rounding...")
        for col, decimals in TABLE_DISPLAY_CONFIG["round"].items():
            if col in df_display.columns:
                df_display[col] = pd.to_numeric(df_display[col], errors="coerce").round(
                    decimals
                )

        # 2. Identify all columns that are NOT samples
        non_sample_cols = set(TABLE_DISPLAY_CONFIG["hide"]) | set(
            TABLE_DISPLAY_CONFIG["relabel"].keys()
        )

        # 3. Identify sample columns
        sample_cols = sorted([col for col in df.columns if col not in non_sample_cols])
        print(f"[DEBUG] Identified {len(sample_cols)} sample columns to format.")

        # Dynamically apply integer rounding and formatting to all sample columns
        for col in sample_cols:
            if col in df_display.columns:
                numeric_col = pd.to_numeric(df_display[col], errors="coerce")
                # Format as an integer with comma separators
                df_display[col] = numeric_col.apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else ""
                )

        # 4. Relabel the columns
        print("[DEBUG] Relabeling columns...")
        df_display.rename(columns=TABLE_DISPLAY_CONFIG["relabel"], inplace=True)

        # 5. Construct the final column order
        final_order = TABLE_DISPLAY_CONFIG["order"] + sample_cols

        # 6. Filter for only the columns that exist and are desired
        existing_cols_to_show = [
            col for col in final_order if col in df_display.columns
        ]

        print(f"[DEBUG] Final columns for display: {existing_cols_to_show}")
        return df_display[existing_cols_to_show]

    def _save_results(self):
        print("[DEBUG] _save_results called.")
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
            print(f"[DEBUG] Saving results to: {save_path}")
            self.results_df.to_csv(save_path, index=False)
            messagebox.showinfo(
                "Success",
                f"Results successfully saved to:\n{os.path.basename(save_path)}",
            )
        except Exception as e:
            print(f"[DEBUG] Save Exception: {e}")
            messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def _update_table(self, df):
        """Formats the DataFrame and then passes it to the ScrollableTable widget."""
        print("[DEBUG] _update_table called.")
        if df is None or df.empty:
            print("[DEBUG] Table DF is empty/None.")
            self.table.update_table(pd.DataFrame())
            return

        print("[DEBUG] Formatting dataframe for display...")
        df_for_display = self._format_df_for_display(df)
        print(f"[DEBUG] Updating table widget with {len(df_for_display)} rows.")
        self.table.update_table(df_for_display)
