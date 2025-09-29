import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import csv

# --- Local Imports ---
# Make sure your configuration file is named PIMMS_Configuration.py
from PIMMS_Configuration import Config

# ============================================================================================
# ❗ CRITICAL: WORKFLOW MODULE IMPORTS ❗
# ============================================================================================
# All your data processing modules should be in a 'modules' subdirectory
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from adduct_checker import find_matching_mass_relationships
from blank_subtraction import (
    define_and_separate_samples,
    perform_blank_subtraction,
    # process_and_combine_files, # This is now replaced by a robust local version
    rename_metadata_columns,
)
from branching_filter import (
    branching_analyze,
    branching_merge,
)
from crude_filters import (
    apply_mass_filter,
    apply_min_intensity_filter,
    apply_rt_filter,
)
from detection_frequency_filter import detection_frequency_filter
from mass_defect_filter import mass_defect_filter
from ML_algorithm_density import fluorinated_density_filter
from monoisotopic_grouper import (
    analyze_adjusted_df as mono_analyze,
    merge_groups_into_adjusted_df as mono_merge,
)
from neutral_loss_checker import find_neutral_loss_matches
from post_source_decay_filter import remove_post_source_decay
from regression_analysis import produce_filtered_df
from removing_standards import remove_standards_library
from single_chromatography import combined_filter_pipeline
from smearing_filter import smearing_filter
from Standard_library_scoring import (
    level_2_library_matching,
    level_5_library_matching,
    load_pfas_library,
)


# ============================================================================================
# WORKFLOW LOGIC
# ============================================================================================
def robust_process_and_combine_files(file_paths):
    """
    Reads and concatenates CSV/TSV files, auto-detecting the delimiter.
    """
    all_data_frames = []
    for fp in file_paths:
        try:
            with open(fp, "r", newline="", encoding="utf-8") as f:
                dialect = csv.Sniffer().sniff(f.readline(), delimiters=",\t")
                delimiter = dialect.delimiter
                print(
                    f"[INFO] Auto-detected delimiter '{repr(delimiter)}' for file {os.path.basename(fp)}"
                )
            df = pd.read_csv(fp, sep=delimiter)
            all_data_frames.append(df)
        except Exception as e:
            raise IOError(
                f"Could not parse the file {fp}. Please ensure it is a valid CSV or TSV file. Error: {e}"
            )

    if not all_data_frames:
        raise ValueError("No data could be loaded from the provided files.")
    return pd.concat(all_data_frames, ignore_index=True)


def run_pimms_workflow(config):
    """
    This function contains the complete data processing pipeline.
    It takes a Config object populated by the GUI and runs the analysis.
    """
    try:
        # --- Pre-run Check ---
        if not config.raw_data_input_location or not os.path.exists(
            config.raw_data_input_location
        ):
            messagebox.showerror(
                "Error",
                f"Input file not found. Please check the path:\n{config.raw_data_input_location}",
            )
            return
        if not config.output_path:
            messagebox.showerror("Error", "Please specify an output file path.")
            return

        print("[INFO] Starting PIMMS workflow...")
        print(f"  - Input File: {config.raw_data_input_location}")
        print(f"  - Output File: {config.output_path}")

        # --- DATA SETUP ---
        print("[INFO] Loading and preparing initial data...")
        combined_data = robust_process_and_combine_files(
            [config.raw_data_input_location]
        )
        combined_data = rename_metadata_columns(combined_data, config.metadata_mapping)
        _, control_df, experimental_df = define_and_separate_samples(
            combined_data,
            config.control_start_col,
            config.control_end_col,
            config.experimental_start_col,
            config.experimental_end_col,
        )
        print("[INFO] Data separation complete.")

        # --- BLANK SUBTRACTION ---
        print(
            f"[INFO] Performing Blank Subtraction (Method: {config.blank_subtraction_method})..."
        )
        adjusted_df, _, _ = perform_blank_subtraction(
            config.blank_subtraction_method,
            control_df,
            experimental_df,
            std_devs=config.blank_subtraction_std_dev,
        )

        # --- FULL FILTERING PIPELINE ---
        print("[INFO] Applying filters to adjusted dataset...")
        adjusted_df = apply_min_intensity_filter(adjusted_df, config.min_intensity)
        adjusted_df = apply_rt_filter(adjusted_df, config.rt_min, config.rt_max)
        adjusted_df = apply_mass_filter(adjusted_df, config.mass_min, config.mass_max)

        adjusted_df = smearing_filter(
            adjusted_df,
            rt_tolerance=config.rt_tolerance,
            ccs_tolerance=config.ccs_tolerance,
        )

        groups = branching_analyze(
            adjusted_df,
            mass_error_ppm=config.mass_error_ppm,
            rt_tolerance=config.rt_tolerance,
            ccs_tolerance=config.ccs_tolerance,
        )
        adjusted_df = branching_merge(groups)

        groups = mono_analyze(
            adjusted_df,
            z_range=range(1, 4),
            mass_error_ppm=config.mass_error_ppm,
            rt_tolerance=config.rt_tolerance,
            ccs_tolerance=config.ccs_tolerance,
        )
        adjusted_df = mono_merge(adjusted_df, groups)

        adjusted_df = fluorinated_density_filter(adjusted_df)
        adjusted_df = mass_defect_filter(
            adjusted_df, config.mass_defect_lower, config.mass_defect_upper
        )
        adjusted_df = detection_frequency_filter(
            adjusted_df, config.frequency_threshold
        )

        adjusted_df = remove_standards_library(
            adjusted_df,
            config.standards_file,
            mass_error_ppm=config.mass_error_ppm,
            ccs_error_percentage=config.ccs_tolerance,
            z=1,
        )

        # --- LIBRARY MATCHING ---
        print("[INFO] Matching features against Level 2 Library...")
        pfas_library = load_pfas_library(config.level_2_library)
        likely_matched_df, likely_unmatched_df = level_2_library_matching(
            adjusted_df,
            pfas_library,
            config.level_2_library_mapping,
            config.mass_error_ppm,
            config.ccs_tolerance,
            config.rt_tolerance,
            config.include_rt_scoring,
        )

        print("[INFO] Matching remaining features against Level 5 Library...")
        external_targets_library = load_pfas_library(config.level_5_library)
        external_matched_df, external_unmatched_df = level_5_library_matching(
            likely_unmatched_df,
            external_targets_library,
            config.level_5_library_mapping,
            config.mass_error_ppm,
        )

        adjusted_df = pd.concat(
            [likely_matched_df, external_matched_df, external_unmatched_df],
            ignore_index=True,
        )

        # --- FINAL ANALYSIS STEPS ---
        adjusted_df = remove_post_source_decay(adjusted_df)

        adjusted_df = produce_filtered_df(
            adjusted_df,
            config.level_2_library,
            config.rt_regression_filter,
            config.ccs_regression_filter,
        )

        library_df = pd.read_csv(config.level_2_library)
        adjusted_df = combined_filter_pipeline(
            adjusted_df, library_df, config.mass_error_ppm
        )

        adjusted_df = find_matching_mass_relationships(adjusted_df)
        adjusted_df = find_neutral_loss_matches(adjusted_df)

        # --- SAVE OUTPUT ---
        output_dir = os.path.dirname(config.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        adjusted_df.to_csv(config.output_path, index=False)

        print(f"[SUCCESS] Final adjusted dataset saved to {config.output_path}")
        messagebox.showinfo(
            "Success",
            f"Workflow completed successfully!\n\nOutput saved to:\n{config.output_path}",
        )

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        messagebox.showerror("Error", f"The workflow failed during processing:\n\n{e}")


# ============================================================================================
# GUI APPLICATION
# ============================================================================================
class PimmsGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PIMMS Workflow Configuration")
        self.geometry("850x700")

        self.config = Config()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self._create_files_tab()
        self._create_mapping_tab()
        self._create_params_tab()
        self._create_run_tab()

    def _create_files_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="File Paths")
        self.file_path_entries = {}
        file_options = {
            "Raw Data Input": "raw_data_input_location",
            "Standards for Removal": "standards_file",
            "Level 2 Library": "level_2_library",
            "Level 5 Library": "level_5_library",
            "Output Report Path": "output_path",
        }
        for i, (text, key) in enumerate(file_options.items()):
            self._create_file_input(tab, text, key, i)

    def _create_mapping_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Column Mappings")
        self.mapping_entries = {}

        def _create_mapping_input(parent, text, key, default, row, col):
            ttk.Label(parent, text=text + ":").grid(
                row=row, column=col * 2, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(parent, width=8)
            entry.insert(0, default)
            entry.grid(row=row, column=col * 2 + 1, padx=5, pady=2, sticky="w")
            self.mapping_entries[key] = entry

        meta_frame = ttk.LabelFrame(
            tab, text="Metadata Column Letters (Raw Data)", padding=(10, 5)
        )
        meta_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.metadata_mapping.items()):
            _create_mapping_input(meta_frame, key, f"meta_{key}", val, i // 3, i % 3)

        sample_frame = ttk.LabelFrame(
            tab, text="Sample Column Ranges (Raw Data)", padding=(10, 5)
        )
        sample_frame.pack(fill="x", padx=10, pady=5)
        _create_mapping_input(
            sample_frame,
            "Control Start",
            "control_start_col",
            self.config.control_start_col,
            0,
            0,
        )
        _create_mapping_input(
            sample_frame,
            "Control End",
            "control_end_col",
            self.config.control_end_col,
            0,
            1,
        )
        _create_mapping_input(
            sample_frame,
            "Experimental Start",
            "experimental_start_col",
            self.config.experimental_start_col,
            1,
            0,
        )
        _create_mapping_input(
            sample_frame,
            "Experimental End",
            "experimental_end_col",
            self.config.experimental_end_col,
            1,
            1,
        )

        l2_frame = ttk.LabelFrame(
            tab, text="Level 2 Library Column Letters", padding=(10, 5)
        )
        l2_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_2_library_mapping.items()):
            _create_mapping_input(l2_frame, key, f"l2_{key}", val, i // 3, i % 3)

        l5_frame = ttk.LabelFrame(
            tab, text="Level 5 Library Column Letters", padding=(10, 5)
        )
        l5_frame.pack(fill="x", padx=10, pady=5)
        for i, (key, val) in enumerate(self.config.level_5_library_mapping.items()):
            _create_mapping_input(l5_frame, key, f"l5_{key}", val, i // 2, i % 2)

    def _create_params_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Parameters")
        self.param_entries = {}

        params_frame = ttk.LabelFrame(
            tab, text="Tolerances and Filters", padding=(10, 5)
        )
        params_frame.pack(fill="x", padx=10, pady=5)

        params = {
            "Mass Error (ppm)": "mass_error_ppm",
            "CCS Tolerance (%)": "ccs_tolerance",
            "RT Tolerance": "rt_tolerance",
            "Min Intensity": "min_intensity",
            "Min RT": "rt_min",
            "Max RT": "rt_max",
        }
        for i, (text, key) in enumerate(params.items()):
            ttk.Label(params_frame, text=text + ":").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(params_frame)
            entry.insert(0, str(getattr(self.config, key)))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.param_entries[key] = entry

        bs_frame = ttk.LabelFrame(tab, text="Blank Subtraction", padding=(10, 5))
        bs_frame.pack(fill="x", padx=10, pady=5, anchor="w")

        ttk.Label(bs_frame, text="Method:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.bs_method_var = tk.StringVar(value=self.config.blank_subtraction_method)
        bs_combo = ttk.Combobox(
            bs_frame,
            textvariable=self.bs_method_var,
            values=["1", "2"],
            state="readonly",
        )
        bs_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(bs_frame, text="Std Deviations (for Method 2):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.std_dev_entry = ttk.Entry(bs_frame)
        self.std_dev_entry.insert(
            0, str(getattr(self.config, "blank_subtraction_std_dev", 3.0))
        )
        self.std_dev_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["blank_subtraction_std_dev"] = self.std_dev_entry

        bs_combo.bind("<<ComboboxSelected>>", self._toggle_std_dev_entry)
        self._toggle_std_dev_entry()

    def _toggle_std_dev_entry(self, event=None):
        if self.bs_method_var.get() == "2":
            self.std_dev_entry.config(state="normal")
        else:
            self.std_dev_entry.config(state="disabled")

    def _create_run_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Run Workflow")
        run_button = ttk.Button(
            tab, text="Run PIMMS Workflow", command=self.run_workflow_thread
        )
        run_button.pack(pady=20)
        self.log_text = tk.Text(tab, height=20, width=80, state="disabled", wrap="word")
        self.log_text.pack(pady=10, padx=10, expand=True, fill="both")
        sys.stdout = TextRedirector(self.log_text, "stdout")

    def _create_file_input(self, parent, label_text, config_key, row):
        ttk.Label(parent, text=label_text + ":").grid(
            row=row, column=0, padx=5, pady=5, sticky="w"
        )
        entry = ttk.Entry(parent, width=70)
        # Populate with default value from config
        default_val = getattr(self.config, config_key, "")
        if isinstance(default_val, list):  # Handle list case for raw data
            default_val = default_val[0] if default_val else ""
        entry.insert(0, default_val)
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.file_path_entries[config_key] = entry
        browse_button = ttk.Button(
            parent,
            text="Browse...",
            command=lambda e=entry, k=config_key: self._browse_file(e, k),
        )
        browse_button.grid(row=row, column=2, padx=5, pady=5)

    def _browse_file(self, entry, key):
        if "output" in key:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
            )
        else:
            filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)

    def run_workflow_thread(self):
        try:
            for key, entry in self.file_path_entries.items():
                setattr(self.config, key, entry.get())
            for key, entry in self.param_entries.items():
                setattr(self.config, key, float(entry.get()))

            self.config.blank_subtraction_method = self.bs_method_var.get()

            self.config.control_start_col = self.mapping_entries[
                "control_start_col"
            ].get()
            self.config.control_end_col = self.mapping_entries["control_end_col"].get()
            self.config.experimental_start_col = self.mapping_entries[
                "experimental_start_col"
            ].get()
            self.config.experimental_end_col = self.mapping_entries[
                "experimental_end_col"
            ].get()

            self.config.metadata_mapping = {
                k: self.mapping_entries[f"meta_{k}"].get()
                for k in self.config.metadata_mapping
            }
            self.config.level_2_library_mapping = {
                k: self.mapping_entries[f"l2_{k}"].get()
                for k in self.config.level_2_library_mapping
            }
            self.config.level_5_library_mapping = {
                k: self.mapping_entries[f"l5_{k}"].get()
                for k in self.config.level_5_library_mapping
            }

            thread = threading.Thread(target=run_pimms_workflow, args=(self.config,))
            thread.daemon = True
            thread.start()
        except ValueError as e:
            messagebox.showerror(
                "Invalid Input",
                f"Please check your parameters. A numeric value is required.\n\nError: {e}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred before starting the workflow: {e}",
            )


class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")

    def flush(self):
        pass


if __name__ == "__main__":
    app = PimmsGUI()
    app.mainloop()
