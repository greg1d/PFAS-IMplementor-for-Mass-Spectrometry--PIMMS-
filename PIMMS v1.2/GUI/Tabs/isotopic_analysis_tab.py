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
        super().__init__(parent)
        self.config = config
        self.pimms_filepath = tk.StringVar()
        self.cef_folder = tk.StringVar()
        self.results_df = None

        self._create_widgets()
        self._load_defaults()

    def _create_widgets(self):
        # --- NEW: Define all help texts in one place for easy editing ---
        help_texts = {
            "pimms_file": "Select the primary input CSV file from the PIMMS processing pipeline. This file should contain the list of all detected features.",
            "cef_folder": "Select any single .cef file from the folder containing all raw data files. The application will automatically use the folder path to find the necessary raw data for isotopic analysis.",
            "run_pipeline": "1. Processes the PIMMS file to find potential halogenated compounds.\n2. Extracts isotopic profiles from the raw .cef files.\n3. Performs heavy halogen analysis.\n4. Calculates Kauffman plot parameters.\n\nThis can take several minutes to complete.",
            "launch_plot": "Generates and opens an interactive Kauffman plot in your web browser. This button is enabled only after the main pipeline has been run successfully.",
            "save_results": "Saves the full data table, including all calculated values, to a CSV file. This button is enabled only after the main pipeline has been run successfully.",
            "results_table": "Displays the final results after the analysis is complete, showing key metrics and classification for each identified feature.",
        }

        control_frame = ttk.Labelframe(self, text="Workflow", padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        control_frame.columnconfigure(1, weight=1)

        table_frame = ttk.Labelframe(self, text="Analysis Results", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- MODIFIED: Added help icons to Input Widgets ---
        ttk.Label(control_frame, text="PIMMS File:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Entry(
            control_frame, textvariable=self.pimms_filepath, state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(
            control_frame, text="Browse...", command=self._select_pimms_file
        ).grid(row=0, column=2, padx=5)
        # NEW: Help icon for PIMMS File
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
        # NEW: Help icon for CEF Folder
        help_cef = ttk.Label(control_frame, text=" (?) ", cursor="question_arrow")
        help_cef.grid(row=1, column=3, sticky="w")
        Tooltip(help_cef, text=help_texts["cef_folder"])

        # --- MODIFIED: Action Buttons now use grid for better layout with icons ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.run_button = ttk.Button(
            action_frame,
            text="1. Run Full Pipeline & Analysis",
            command=self._run_pipeline_thread,
            state="disabled",
        )
        self.run_button.grid(row=0, column=0, padx=(0, 2))
        # NEW: Help icon for Run button
        help_run = ttk.Label(action_frame, text=" (?) ", cursor="question_arrow")
        help_run.grid(row=0, column=1, padx=(0, 10))
        Tooltip(help_run, text=help_texts["run_pipeline"])

        self.plot_button = ttk.Button(
            action_frame,
            text="2. Generate Kauffman Plot",
            command=self._launch_plot,
            state="disabled",
        )
        self.plot_button.grid(row=0, column=2, padx=(0, 2))
        # NEW: Help icon for Plot button
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
        # NEW: Help icon for Save button
        help_save = ttk.Label(action_frame, text=" (?) ", cursor="question_arrow")
        help_save.grid(row=0, column=5, padx=(0, 10))
        Tooltip(help_save, text=help_texts["save_results"])

        # --- MODIFIED: Added a help icon to the results table frame ---
        self.table = ScrollableTable(table_frame)
        self.table.pack(fill="both", expand=True)
        # NEW: Help icon for the table itself
        help_table = ttk.Label(table_frame, text=" (?) ", cursor="question_arrow")
        help_table.place(relx=1.0, rely=0.0, x=-5, y=-8, anchor="ne")
        Tooltip(help_table, text=help_texts["results_table"])

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
        """
        Opens a file dialog to select any .cef file, then extracts the
        parent folder path from it.
        """
        filepath = filedialog.askopenfilename(
            title="Select any .cef file in the target folder",
            filetypes=[("CEF Files", "*.cef"), ("All files", "*.*")],
        )

        if filepath:
            # The pipeline needs the folder, not the file.
            # os.path.dirname() extracts the directory path from a full file path.
            folder_path = os.path.dirname(filepath)
            self.cef_folder.set(folder_path)
            self._check_inputs()

    # --- End of Modification ---

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
            grid_path = resource_path("PIMMS v1.2/data/kaufman_grid_data.npz")
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
                resource_path("PIMMS v1.2/data/kaufman_contour_boundaries_SMOOTH.csv"),
                resource_path("PIMMS v1.2/data/kaufman_grid_data.npz"),
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
        max_len = 35
        if "Match_ID" in df_display.columns:
            df_display["Match_ID"] = (
                df_display["Match_ID"]
                .astype(str)
                .apply(lambda x: (x[: max_len - 3] + "...") if len(x) > max_len else x)
            )
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
        """Formats the DataFrame and then passes it to the ScrollableTable widget."""
        if df is None or df.empty:
            self.table.update_table(pd.DataFrame())
            return
        df_for_display = self._format_df_for_display(df)
        self.table.update_table(df_for_display)
