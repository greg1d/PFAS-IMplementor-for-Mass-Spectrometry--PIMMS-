import os
import sys
import tkinter.messagebox as messagebox
import pandas as pd
import csv
import traceback

# Add the 'modules' subdirectory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# All data processing imports
from adduct_checker import find_matching_mass_relationships  # type: ignore
from blank_subtraction import (  # type: ignore
    define_and_separate_samples,
    perform_blank_subtraction,
)
from branching_filter import branching_analyze, branching_merge  # type: ignore
from crude_filters import (  # type: ignore
    apply_mass_filter,
    apply_min_intensity_filter,
    apply_rt_filter,
)
from detection_frequency_filter import detection_frequency_filter  # type: ignore
from mass_defect_filter import mass_defect_filter  # type: ignore
from ML_algorithm_density import fluorinated_density_filter  # type: ignore
from monoisotopic_grouper import (  # type: ignore
    analyze_adjusted_df as mono_analyze,
    merge_groups_into_adjusted_df as mono_merge,
)
from neutral_loss_checker import find_neutral_loss_matches  # type: ignore
from post_source_decay_filter import remove_post_source_decay  # type: ignore
from regression_analysis import produce_filtered_df  # type: ignore
from removing_standards import remove_standards_library  # type: ignore
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
    # This function is unchanged
    # ...
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
        # --- Pre-run Check (unchanged) ---
        if not config.raw_data_input_location or not os.path.exists(
            config.raw_data_input_location
        ):
            messagebox.showerror(
                "Error", f"Input file not found:\n{config.raw_data_input_location}"
            )
            return
        # ...

        # --- DATA LOADING ---
        combined_data = robust_process_and_combine_files(
            [config.raw_data_input_location]
        )
        pfas_library = load_pfas_library(config.level_2_library)
        external_targets_library = load_pfas_library(config.level_5_library)
        standards_df = pd.read_csv(config.standards_file)

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
        config.clean_l5_map = {
            k: external_targets_library.columns[column_letter_to_index(v)]
            for k, v in config.level_5_library_mapping.items()
            if column_letter_to_index(v) < len(external_targets_library.columns)
        }

        # --- FIX: Added standardization for Standards Library ---
        config.clean_standards_map = {
            k: standards_df.columns[column_letter_to_index(v)]
            for k, v in config.standards_library_mapping.items()
            if column_letter_to_index(v) < len(standards_df.columns)
        }

        # Rename all DataFrames to use standard keys
        combined_data.rename(
            columns={v: k for k, v in config.clean_metadata_map.items()}, inplace=True
        )
        pfas_library.rename(
            columns={v: k for k, v in config.clean_l2_map.items()}, inplace=True
        )
        external_targets_library.rename(
            columns={v: k for k, v in config.clean_l5_map.items()}, inplace=True
        )
        standards_df.rename(
            columns={v: k for k, v in config.clean_standards_map.items()}, inplace=True
        )

        # --- DATA SEPARATION (unchanged) ---
        _, control_df, experimental_df, metadata_cols = define_and_separate_samples(
            combined_data,
            config.control_start_col,
            config.control_end_col,
            config.experimental_start_col,
            config.experimental_end_col,
        )

        # --- BLANK SUBTRACTION (unchanged) ---

        adjusted_df = perform_blank_subtraction(
            method=config.blank_subtraction_method,
            control_df=control_df,
            experimental_df=experimental_df,
            metadata_cols=metadata_cols,  # Pass the list of metadata columns
            std_devs=config.blank_subtraction_std_dev,
        )
        # --- FULL FILTERING PIPELINE (RESTORED & CORRECTED) ---
        adjusted_df = apply_min_intensity_filter(
            adjusted_df, metadata_cols, config.min_intensity
        )

        adjusted_df = apply_rt_filter(adjusted_df, config.rt_min, config.rt_max)

        adjusted_df = apply_mass_filter(adjusted_df, config.mz_min, config.mz_max)

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

        adjusted_df = branching_merge(
            group_dfs=groups, original_df=adjusted_df, metadata_cols=metadata_cols
        )
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
            adjusted_df,
            lower_mass_filter_bound=config.mass_defect_lower_bound,
            upper_mass_filter_bound=config.mass_defect_upper_bound,
        )
        adjusted_df = detection_frequency_filter(
            adjusted_df, metadata_cols, config.frequency_threshold
        )
        # --- FIX: The call now passes the prepared 'standards_df' DataFrame ---
        adjusted_df = remove_standards_library(
            adjusted_df,
            standards_df,
            mass_error_ppm=config.mass_error_ppm,
            ccs_error_percentage=config.ccs_tolerance,
            z=1,
        )

        # Using keyword arguments for clarity and safety
        likely_matched_df, likely_unmatched_df = level_2_library_matching(
            adjusted_df=adjusted_df,
            metadata_cols=metadata_cols,
            pfas_library=pfas_library,
            mass_error_ppm=config.mass_error_ppm,
            ccs_tolerance=config.ccs_tolerance,
            rt_tolerance=config.rt_tolerance,
            include_rt_scoring=config.include_rt_scoring,
        )

        # --- 2. Perform Level 5 Library Matching on the remaining features ---
        external_matched_df, external_unmatched_df = level_5_library_matching(
            unmatched_df=likely_unmatched_df,
            metadata_cols=metadata_cols,
            external_targets_library=external_targets_library,
            mass_error_ppm=config.mass_error_ppm,
        )

        # --- 3. Consolidate all results into a single DataFrame ---
        # First, define the list of all DataFrames to be combined
        dfs_to_concat = [
            likely_matched_df,
            external_matched_df,
            external_unmatched_df,
        ]

        # Next, create a new list of cleaned DataFrames, removing duplicate columns
        cleaned_dfs = []
        for df in dfs_to_concat:
            if not df.empty:
                # This keeps the first occurrence of any column name and drops duplicates
                cleaned_df = df.loc[:, ~df.columns.duplicated(keep="first")]
                cleaned_dfs.append(cleaned_df)

        # Finally, concatenate the cleaned DataFrames
        if cleaned_dfs:
            adjusted_df = pd.concat(cleaned_dfs, ignore_index=True)
        else:
            # Handle the edge case where all processing resulted in empty DataFrames
            adjusted_df = pd.DataFrame()

        # --- FINAL ANALYSIS STEPS (Now correctly indented) ---
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

        print(adjusted_df)
        messagebox.showinfo(
            "Success",
            f"Workflow completed successfully!\n\nOutput saved to:\n{config.output_path}",
        )

    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        traceback.print_exc()
        messagebox.showerror("Error", f"The workflow failed during processing:\n\n{e}")
