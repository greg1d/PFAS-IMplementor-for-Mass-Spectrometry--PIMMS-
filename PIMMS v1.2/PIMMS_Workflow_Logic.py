import csv
import os
import sys
import tkinter.messagebox as messagebox
import traceback

import pandas as pd

# Add the 'modules' subdirectory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# All data processing imports
from adduct_checker import adduct_removal  # type: ignore
from blank_subtraction import (  # type: ignore
    define_and_separate_samples,
    perform_blank_subtraction,
)
from crude_filters import (  # type: ignore
    apply_mass_filter,
    apply_min_intensity_filter,
    apply_rt_filter,
)
from detection_frequency_and_abundance import (  # type: ignore
    average_abundance,
    detection_frequency_calculation,
)
from detection_frequency_filter import detection_frequency_filter  # type: ignore
from grouper import flag_and_merge_duplicates  # type: ignore
from M2_identifier import remove_Cl_Br_M2_signal  # type: ignore
from mass_defect_filter import mass_defect_filter  # type: ignore
from ML_algorithm_density import fluorinated_density_filter  # type: ignore
from neutral_loss_checker import find_neutral_loss_matches  # type: ignore
from post_source_decay_filter import remove_post_source_decay  # type: ignore
from regression_analysis import produce_filtered_df  # type: ignore
from removing_standards import remove_standards_library  # type: ignore
from rounding import significant_figures_rounding  # type: ignore
from single_chromatography import combined_filter_pipeline  # type: ignore
from smearing_filter import smearing_filter  # type: ignore
from Standard_library_scoring import (  # type: ignore
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
    all_data_frames = []
    for fp in file_paths:
        try:
            with open(fp, "r", newline="", encoding="utf-8") as f:
                dialect = csv.Sniffer().sniff(f.readline(), delimiters=",\t")
                delimiter = dialect.delimiter
            df = pd.read_csv(fp, sep=delimiter)
            all_data_frames.append(df)
        except Exception as e:
            raise IOError(f"Could not parse the file {fp}. Error: {e}")
    if not all_data_frames:
        raise ValueError("No data could be loaded.")
    return pd.concat(all_data_frames, ignore_index=True)


def run_pimms_workflow(config):
    """
    This function contains the complete data processing pipeline.
    """
    try:
        # --- Pre-run Check ---
        if not config.raw_data_input_location or not os.path.exists(
            config.raw_data_input_location
        ):
            messagebox.showerror(
                "Error", f"Input file not found:\n{config.raw_data_input_location}"
            )
            return

        # --- DATA LOADING ---
        combined_data = robust_process_and_combine_files(
            [config.raw_data_input_location]
        )
        print(f"DEBUG: Initial Loaded Features: {len(combined_data)}")

        # --- SAFE LOAD: Level 2 Library (Critical) ---
        if not getattr(config, "level_2_library", ""):
            raise ValueError(
                "The 'Level 2 Library' file path is missing. This file is required."
            )
        pfas_library = load_pfas_library(config.level_2_library)

        # --- SAFE LOAD: Level 5 Library (Optional) ---
        if getattr(config, "level_5_library", ""):
            external_targets_library = load_pfas_library(config.level_5_library)
        else:
            print(
                "DEBUG: Level 5 Library path is blank. Proceeding with empty L5 library."
            )
            # Create empty DF with expected columns to prevent errors later
            external_targets_library = pd.DataFrame(
                columns=["m/z", "Name", "Adduct", "CCS", "RT"]
            )

        # --- SAFE LOAD: Standards Library (Conditional) ---
        # 1. Check if user wants to ignore it
        if getattr(config, "ignore_standards", False):
            print("DEBUG: Standards Library ignored by user configuration.")
            standards_df = pd.DataFrame()
        # 2. Check if path is provided
        elif getattr(config, "standards_file", ""):
            try:
                standards_df = pd.read_csv(config.standards_file)
            except Exception as e:
                print(f"[WARNING] Could not load standards file: {e}")
                standards_df = pd.DataFrame()
        # 3. Path is blank but 'Ignore' wasn't checked -> Treat as empty/ignored safely
        else:
            print(
                "DEBUG: Standards file path is blank. Proceeding without standards removal."
            )
            standards_df = pd.DataFrame()

        # --- CENTRALIZED TRANSLATION & RENAMING LOGIC ---

        config.clean_metadata_map = {
            k: combined_data.columns[column_letter_to_index(v)]
            for k, v in config.metadata_mapping.items()
            if column_letter_to_index(v) < len(combined_data.columns)
        }
        config.clean_l2_map = {
            k: pfas_library.columns[column_letter_to_index(v)]
            for k, v in config.level_2_library_mapping.items()
            if column_letter_to_index(v) < len(pfas_library.columns)
        }

        # Only map L5 if it has columns (it might be the empty placeholder)
        if not external_targets_library.empty:
            config.clean_l5_map = {
                k: external_targets_library.columns[column_letter_to_index(v)]
                for k, v in config.level_5_library_mapping.items()
                if column_letter_to_index(v) < len(external_targets_library.columns)
            }
        else:
            config.clean_l5_map = {}

        # Only map Standards if it has data
        if not standards_df.empty:
            config.clean_standards_map = {
                k: standards_df.columns[column_letter_to_index(v)]
                for k, v in config.standards_library_mapping.items()
                if column_letter_to_index(v) < len(standards_df.columns)
            }
        else:
            config.clean_standards_map = {}

        # Rename all DataFrames to use standard keys
        combined_data.rename(
            columns={v: k for k, v in config.clean_metadata_map.items()}, inplace=True
        )
        pfas_library.rename(
            columns={v: k for k, v in config.clean_l2_map.items()}, inplace=True
        )

        if not external_targets_library.empty:
            external_targets_library.rename(
                columns={v: k for k, v in config.clean_l5_map.items()}, inplace=True
            )

        if not standards_df.empty:
            standards_df.rename(
                columns={v: k for k, v in config.clean_standards_map.items()},
                inplace=True,
            )

        # --- DATA SEPARATION ---
        _, control_df, experimental_df, metadata_cols = define_and_separate_samples(
            combined_data,
            config.control_start_col,
            config.control_end_col,
            config.experimental_start_col,
            config.experimental_end_col,
        )

        # --- BLANK SUBTRACTION ---
        adjusted_df = perform_blank_subtraction(
            method=config.blank_subtraction_method,
            control_df=control_df,
            experimental_df=experimental_df,
            metadata_cols=metadata_cols,
            std_devs=config.blank_subtraction_std_dev,
        )
        print(f"DEBUG: After Blank Subtraction: {len(adjusted_df)}")

        # --- FULL FILTERING PIPELINE ---
        adjusted_df = apply_min_intensity_filter(
            adjusted_df, metadata_cols, config.min_intensity
        )
        print(f"DEBUG: After Min Intensity Filter: {len(adjusted_df)}")

        adjusted_df = apply_rt_filter(adjusted_df, config.rt_min, config.rt_max)
        print(f"DEBUG: After RT Filter: {len(adjusted_df)}")

        adjusted_df = apply_mass_filter(adjusted_df, config.mz_min, config.mz_max)
        print(f"DEBUG: After Mass Filter: {len(adjusted_df)}")

        adjusted_df = smearing_filter(
            adjusted_df,
            rt_tolerance=config.rt_tolerance,
            ccs_tolerance=config.ccs_tolerance,
        )
        print(f"DEBUG: After Smearing Filter: {len(adjusted_df)}")

        adjusted_df = flag_and_merge_duplicates(
            adjusted_df,
            mass_error_ppm=config.mass_error_ppm,
            ccs_tolerance=config.ccs_tolerance,
            rt_tolerance=config.rt_tolerance,
        )
        print(f"DEBUG: After Duplicate Merge: {len(adjusted_df)}")

        adjusted_df = fluorinated_density_filter(adjusted_df)
        print(f"DEBUG: After Fluorinated Density Filter: {len(adjusted_df)}")

        adjusted_df = mass_defect_filter(
            adjusted_df,
            lower_mass_filter_bound=config.mass_defect_lower_bound,
            upper_mass_filter_bound=config.mass_defect_upper_bound,
        )
        print(f"DEBUG: After Mass Defect Filter: {len(adjusted_df)}")

        adjusted_df = detection_frequency_filter(
            adjusted_df, metadata_cols, config.frequency_threshold
        )
        print(f"DEBUG: After Detection Frequency Filter: {len(adjusted_df)}")

        # --- LEVEL 2 MATCHING ---
        likely_matched_df, likely_unmatched_df = level_2_library_matching(
            adjusted_df=adjusted_df,
            metadata_cols=metadata_cols,
            pfas_library=pfas_library,
            mass_error_ppm=config.mass_error_ppm,
            ccs_tolerance=config.ccs_tolerance,
            rt_tolerance=config.rt_tolerance,
            include_rt_scoring=config.include_rt_scoring,
        )
        print(
            f"DEBUG: After L2 Matching - Matched: {len(likely_matched_df)}, Unmatched: {len(likely_unmatched_df)}"
        )

        # --- LEVEL 5 MATCHING ---
        if not external_targets_library.empty:
            external_matched_df, external_unmatched_df = level_5_library_matching(
                unmatched_df=likely_unmatched_df,
                metadata_cols=metadata_cols,
                external_targets_library=external_targets_library,
                mass_error_ppm=config.mass_error_ppm,
            )
            print(
                f"DEBUG: After L5 Matching - Matched: {len(external_matched_df)}, Unmatched: {len(external_unmatched_df)}"
            )
        else:
            # If no L5 library, everything unmatched remains unmatched
            external_matched_df = pd.DataFrame()
            external_unmatched_df = likely_unmatched_df
            print("DEBUG: L5 Library empty, skipping L5 matching.")

        # --- CONSOLIDATE RESULTS ---
        dfs_to_concat = [
            likely_matched_df,
            external_matched_df,
            external_unmatched_df,
        ]

        cleaned_dfs = []
        for df in dfs_to_concat:
            if not df.empty:
                cleaned_df = df.loc[:, ~df.columns.duplicated(keep="first")]
                cleaned_dfs.append(cleaned_df)

        if cleaned_dfs:
            adjusted_df = pd.concat(cleaned_dfs, ignore_index=True)
        else:
            adjusted_df = pd.DataFrame()

        print(f"DEBUG: After Re-Concatenation: {len(adjusted_df)}")

        # --- CONDITIONAL STANDARDS REMOVAL ---
        if not getattr(config, "ignore_standards", False) and not standards_df.empty:
            adjusted_df = remove_standards_library(
                adjusted_df,
                standards_df,
                mass_error_ppm=config.mass_error_ppm,
                ccs_error_percentage=config.ccs_tolerance,
            )
            print(f"DEBUG: After Remove Standards: {len(adjusted_df)}")
        else:
            print("DEBUG: Skipped Standards Removal (Ignored or Empty Library)")

        # --- FINAL ANALYSIS STEPS ---
        adjusted_df = remove_post_source_decay(adjusted_df)
        print(f"DEBUG: After Post Source Decay: {len(adjusted_df)}")

        adjusted_df = produce_filtered_df(
            df=adjusted_df,
            config=config,
            level_2_library=config.level_2_library,
            rt_regression_filter=config.rt_regression_filter,
            ccs_regression_filter=config.ccs_regression_filter,
        )
        print(f"DEBUG: After Regression Analysis: {len(adjusted_df)}")

        adjusted_df = combined_filter_pipeline(
            adjusted_df, pfas_library, config.mass_error_ppm
        )
        print(f"DEBUG: After Combined Filter Pipeline: {len(adjusted_df)}")

        adjusted_df = adduct_removal(adjusted_df)
        print(f"DEBUG: After Adduct Removal: {len(adjusted_df)}")

        adjusted_df = find_neutral_loss_matches(adjusted_df)
        print(f"DEBUG: After Neutral Loss Matches: {len(adjusted_df)}")

        # --- SAVE OUTPUT ---
        output_dir = os.path.dirname(config.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        adjusted_df = detection_frequency_calculation(adjusted_df)
        adjusted_df = average_abundance(adjusted_df)
        adjusted_df = significant_figures_rounding(adjusted_df)
        adjusted_df = remove_Cl_Br_M2_signal(
            adjusted_df,
            mass_error_ppm=config.mass_error_ppm,
            ccs_tolerance_percent=config.ccs_tolerance,
            rt_tolerance=config.rt_tolerance,
        )
        print(f"DEBUG: Final Count After Cl/Br Removal: {len(adjusted_df)}")

        adjusted_df.to_csv(config.output_path, index=False)

        print(adjusted_df)
        messagebox.showinfo(
            "Success",
            f"Workflow completed successfully!\n\nOutput saved to:\n{config.output_path}",
        )

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        traceback.print_exc()
        messagebox.showerror("Error", f"The workflow failed during processing:\n\n{e}")
