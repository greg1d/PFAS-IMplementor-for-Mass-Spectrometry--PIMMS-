import os
import sys
import tkinter.messagebox as messagebox
import pandas as pd
import csv
import traceback

# Add the 'modules' subdirectory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# All data processing imports
from adduct_checker import find_matching_mass_relationships
from blank_subtraction import (
    define_and_separate_samples,
    perform_blank_subtraction,
)
from crude_filters import (
    apply_min_intensity_filter,
)
from neutral_loss_checker import find_neutral_loss_matches
from post_source_decay_filter import remove_post_source_decay
from regression_analysis import produce_filtered_df
from removing_standards import remove_standards_library
from single_chromatography import combined_filter_pipeline
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
    # This function is unchanged
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
                f"Could not parse the file {fp}. Please ensure it is a valid CSV or TSV. Error: {e}"
            )
    if not all_data_frames:
        raise ValueError("No data could be loaded from the provided files.")
    return pd.concat(all_data_frames, ignore_index=True)


def run_pimms_workflow(config):
    """
    This function contains the complete data processing pipeline.
    """
    try:
        # --- Pre-run Check (unchanged) ---
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

        # --- DATA LOADING ---
        print("[INFO] Loading and preparing initial data...")
        combined_data = robust_process_and_combine_files(
            [config.raw_data_input_location]
        )
        pfas_library = load_pfas_library(config.level_2_library)
        external_targets_library = load_pfas_library(config.level_5_library)

        # --- CENTRALIZED TRANSLATION & RENAMING LOGIC ---
        print("[INFO] Translating column mappings and standardizing column names...")

        # 1. Create clean maps of {standard_key: actual_column_name}
        config.clean_metadata_map = {}
        for key, col_letter in config.metadata_mapping.items():
            col_index = column_letter_to_index(col_letter)
            if col_index < len(combined_data.columns):
                config.clean_metadata_map[key] = combined_data.columns[col_index]

        config.clean_l2_map = {}
        for key, col_letter in config.level_2_library_mapping.items():
            col_index = column_letter_to_index(col_letter)
            if col_index < len(pfas_library.columns):
                config.clean_l2_map[key] = pfas_library.columns[col_index]

        # --- ADDED: Standardization for Level 5 Library ---
        config.clean_l5_map = {}
        for key, col_letter in config.level_5_library_mapping.items():
            col_index = column_letter_to_index(col_letter)
            if col_index < len(external_targets_library.columns):
                config.clean_l5_map[key] = external_targets_library.columns[col_index]

        # 2. Rename DataFrame columns to the standard keys for universal use
        metadata_rename_map = {v: k for k, v in config.clean_metadata_map.items()}
        combined_data.rename(columns=metadata_rename_map, inplace=True)

        l2_rename_map = {v: k for k, v in config.clean_l2_map.items()}
        pfas_library.rename(columns=l2_rename_map, inplace=True)

        l5_rename_map = {v: k for k, v in config.clean_l5_map.items()}
        external_targets_library.rename(columns=l5_rename_map, inplace=True)

        print("[DEBUG] Main data columns renamed to standard keys.")
        print(
            f"[DEBUG] Level 2 library columns renamed to: {pfas_library.columns.tolist()}"
        )
        print(
            f"[DEBUG] Level 5 library columns renamed to: {external_targets_library.columns.tolist()}"
        )

        # --- DATA SEPARATION (unchanged) ---
        _, control_df, experimental_df = define_and_separate_samples(
            combined_data,
            config.control_start_col,
            config.control_end_col,
            config.experimental_start_col,
            config.experimental_end_col,
        )
        print("[INFO] Data separation complete.")

        # --- BLANK SUBTRACTION (unchanged) ---
        print(
            f"[INFO] Performing Blank Subtraction (Method: {config.blank_subtraction_method})..."
        )
        adjusted_df, _, _ = perform_blank_subtraction(
            config.blank_subtraction_method,
            control_df,
            experimental_df,
            std_devs=config.blank_subtraction_std_dev,
        )

        # --- FULL FILTERING PIPELINE (unchanged) ---
        print("[INFO] Applying filters to adjusted dataset...")
        adjusted_df = apply_min_intensity_filter(adjusted_df, config.min_intensity)
        # ... (rest of filtering)
        adjusted_df = remove_standards_library(
            adjusted_df,
            config.standards_file,
            mass_error_ppm=config.mass_error_ppm,
            ccs_error_percentage=config.ccs_tolerance,
            z=1,
        )

        # --- LIBRARY MATCHING ---
        print("[INFO] Matching features against Level 2 Library...")
        # --- CHANGED: Removed the mapping dictionary argument ---
        likely_matched_df, likely_unmatched_df = level_2_library_matching(
            adjusted_df,
            pfas_library,  # Use the renamed library dataframe
            config.mass_error_ppm,
            config.ccs_tolerance,
            config.rt_tolerance,
            config.include_rt_scoring,
        )

        print("[INFO] Matching remaining features against Level 5 Library...")
        # --- CHANGED: Removed the mapping dictionary argument ---
        external_matched_df, external_unmatched_df = level_5_library_matching(
            likely_unmatched_df,
            external_targets_library,  # Use the renamed library dataframe
            config.mass_error_ppm,
        )

        adjusted_df = pd.concat(
            [likely_matched_df, external_matched_df, external_unmatched_df],
            ignore_index=True,
        )

        # --- FINAL ANALYSIS STEPS (unchanged) ---
        adjusted_df = remove_post_source_decay(adjusted_df)

        adjusted_df = produce_filtered_df(
            df=adjusted_df,
            config=config,
            level_2_library=config.level_2_library,
            rt_regression_filter=config.rt_regression_filter,
            ccs_regression_filter=config.ccs_regression_filter,
        )

        adjusted_df = combined_filter_pipeline(
            adjusted_df, pfas_library, config.mass_error_ppm
        )
        adjusted_df = find_matching_mass_relationships(adjusted_df)
        adjusted_df = find_neutral_loss_matches(adjusted_df)

        # --- SAVE OUTPUT (unchanged) ---
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
