import os
import sys
import tkinter.messagebox as messagebox
import pandas as pd
import csv
import traceback

# Add the 'modules' subdirectory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# All data processing imports are now cleanly located in this file
from adduct_checker import find_matching_mass_relationships
from blank_subtraction import (
    define_and_separate_samples,
    perform_blank_subtraction,
    rename_metadata_columns,
)
from branching_filter import branching_analyze, branching_merge
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
# HELPER AND WORKFLOW LOGIC
# ============================================================================================
def column_letter_to_index(letter):
    """Converts an Excel-style column letter to a zero-based integer index."""
    letter = letter.upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


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
            adjusted_df, config.mass_defect_lower_bound, config.mass_defect_upper_bound
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

        # --- LIBRARY LOADING AND MATCHING ---
        print("[INFO] Loading libraries...")
        pfas_library = load_pfas_library(config.level_2_library)
        external_targets_library = load_pfas_library(config.level_5_library)

        print("[INFO] Matching features against Level 2 Library...")
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

        all_lib_columns = pfas_library.columns.tolist()
        rename_map = {}
        standard_column_names = {
            "name": "PrecursorName",
            "adduct": "PrecursorAdduct",
            "ccs": "PrecursorCCS",
            "rt": "PrecursorRT",
            "mz": "PrecursorMz",
        }
        for key, letter in config.level_2_library_mapping.items():
            if key in standard_column_names:
                index = column_letter_to_index(letter)
                if index < len(all_lib_columns):
                    actual_name = all_lib_columns[index]
                    expected_name = standard_column_names[key]
                    rename_map[actual_name] = expected_name
        library_df_renamed = pfas_library.rename(columns=rename_map)

        adjusted_df = produce_filtered_df(
            adjusted_df,
            config.level_2_library,
            config.rt_regression_filter,
            config.ccs_regression_filter,
        )
        adjusted_df = combined_filter_pipeline(
            adjusted_df, library_df_renamed, config.mass_error_ppm
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
        traceback.print_exc()
        messagebox.showerror("Error", f"The workflow failed during processing:\n\n{e}")
