import traceback

import pandas as pd

# Import all the necessary analysis modules from their respective files
# Ensure these files are in the same directory or your Python path is set correctly.
try:
    from .ccsvmz_analysis import SLOPE_VALIDATOR, process_all_groups
    from .repeat_unit_analysis import (
        mz_group_refinement,  # Make sure this is the simplified version
        mz_repeating_unit_analysis,
        stack_library_with_adjusted,
        validate_ransac_trends,  # Make sure you've added the new function
    )
except ImportError:
    # Fallback for running script directly
    from ccsvmz_analysis import SLOPE_VALIDATOR, process_all_groups
    from repeat_unit_analysis import (
        mz_group_refinement,
        mz_repeating_unit_analysis,
        stack_library_with_adjusted,
        validate_ransac_trends,
    )


def significant_figures_rounding(df):
    """
    Rounds specific columns in a DataFrame to a set number of decimal places.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    print("df going into the rounding def", df.columns)
    df_rounded = df.copy()
    rounding_rules = {"CCS": 1, "RT": 1, "m/z": 4, "DT": 2}
    for column, places in rounding_rules.items():
        if column in df_rounded.columns and pd.api.types.is_numeric_dtype(
            df_rounded[column]
        ):
            df_rounded[column] = df_rounded[column].round(decimals=places)
    return df_rounded


def standardize_columns(df, file_type="Library", **kwargs):
    """
    Standardizes column names based on user input, which can be either a
    column name (e.g., "Mass") or a column position (e.g., "B").

    It will only map 'Average Abundance' and 'Detection Frequency (%)' if the
    file_type is 'Experimental'.

    Args:
        df (pd.DataFrame): The input DataFrame with original headers.
        file_type (str): Label for error messages ('Library' or 'Experimental').
        **kwargs: Mapping of standard_name=user_identifier (e.g., mz_col_pos='B').

    Returns:
        pd.DataFrame: DataFrame with standardized column names.
    """
    rename_map = {}

    # UPDATED: The dictionary now includes the new standard names.
    standard_names = {
        "name_col_pos": "Name",
        "mz_col_pos": "m/z",
        "ccs_col_pos": "CCS",
        "rt_col_pos": "RT",
        "id_col_pos": "ID",
        "avg_abundance_col_pos": "Average Abundance",
        "det_frequency_col_pos": "Detection Frequency (%)",
    }

    for key, user_identifier in kwargs.items():
        if not user_identifier:  # Skip if the user left the input box blank
            continue

        # --- NEW: Conditional logic for experimental-only columns ---
        # If the key is for abundance or frequency, but the file is not the
        # experimental file, skip this iteration of the loop.
        if (
            key in ["avg_abundance_col_pos", "det_frequency_col_pos"]
            and file_type != "Experimental"
        ):
            continue
        # -----------------------------------------------------------

        standard_name = standard_names[key]
        original_col_name = None

        # Check if the identifier is a column POSITION (e.g., "A", "B")
        if (
            isinstance(user_identifier, str)
            and len(user_identifier) == 1
            and user_identifier.isalpha()
        ):
            col_idx = ord(user_identifier.upper()) - ord("A")
            if 0 <= col_idx < len(df.columns):
                original_col_name = df.columns[col_idx]
            else:
                raise ValueError(
                    f"Column mapping error in {file_type} file: Position '{user_identifier}' (Index {col_idx}) is out of range. "
                    f"The file only has {len(df.columns)} columns."
                )
        # Otherwise, assume the identifier is a column NAME
        else:
            if user_identifier in df.columns:
                original_col_name = user_identifier
            else:
                raise ValueError(
                    f"Column mapping error in {file_type} file: Column name '{user_identifier}' not found. "
                    f"Available columns are: {df.columns.tolist()}"
                )

        if original_col_name:
            rename_map[original_col_name] = standard_name

    return df.rename(columns=rename_map)


def run_analysis_pipeline(
    experimental_filepath,
    library_filepath,
    selected_repeating_units,
    mass_error_ppm,
    min_valid_points,
    min_library_points,
    ransac_threshold_percentage,
    min_ransac_samples,
    library_name_col_pos,
    library_mz_col_pos,
    library_ccs_col_pos,
    library_rt_col_pos,
    library_id_col_pos,
    exp_name_col_pos,
    exp_mz_col_pos,
    exp_ccs_col_pos,
    exp_rt_col_pos,
    exp_id_col_pos,
    slope_range=(0.05, 0.25),
):
    """
    Orchestrates the entire analysis workflow from file loading to RANSAC,
    including all validation parameters.
    """
    print("\n==============================================")
    print("====== RUNNING FULL ANALYSIS PIPELINE ======")
    print("==============================================")

    try:
        # Step 1: Load Data, PRESERVING Original Headers
        print("\n[Step 1] Loading data with original headers...")
        experimental_data_df = pd.read_csv(experimental_filepath)
        library_data_df = pd.read_csv(library_filepath)

        # Step 1.5: Map Columns using the new flexible method
        print("\n[Step 1.5] Standardizing columns by name or position...")

        # Pass all the user inputs from the GUI to the new function
        library_data_df = standardize_columns(
            library_data_df,
            file_type="Library",
            name_col_pos=library_name_col_pos,
            mz_col_pos=library_mz_col_pos,
            ccs_col_pos=library_ccs_col_pos,
            rt_col_pos=library_rt_col_pos,
            id_col_pos=library_id_col_pos,
        )
        experimental_data_df = standardize_columns(
            experimental_data_df,
            file_type="Experimental",
            name_col_pos=exp_name_col_pos,
            mz_col_pos=exp_mz_col_pos,
            ccs_col_pos=exp_ccs_col_pos,
            rt_col_pos=exp_rt_col_pos,
            id_col_pos=exp_id_col_pos,
        )

        # Step 1.7: Harmonize Columns (add placeholders if still missing)
        print("\n[Step 1.7] Harmonizing columns before stacking...")
        if "ID" not in experimental_data_df.columns:
            raise ValueError(
                "An 'ID' column must be specified for the experimental file."
            )
        if "ID" not in library_data_df.columns:
            library_data_df["ID"] = 0
        if "RT" not in library_data_df.columns:
            library_data_df["RT"] = pd.NA
        if "RT" not in experimental_data_df.columns:
            experimental_data_df["RT"] = pd.NA
        print(experimental_data_df.columns)
        stacked_df = stack_library_with_adjusted(experimental_data_df, library_data_df)
        print("Columns after stacking:", stacked_df.columns)
        if stacked_df is None or stacked_df.empty:
            raise ValueError("Data stacking resulted in an empty DataFrame.")

        # --- Step 3: Find Homologous Series ---
        print("\n[Step 3] Finding homologous series...")
        mass_groups = mz_repeating_unit_analysis(
            stacked_df,
            selected_repeating_units,
            mass_error_ppm=mass_error_ppm,
        )
        if mass_groups.empty:
            print("[PIPELINE INFO] No initial homologous groups were found.")
            return pd.DataFrame()
        print("mass groups columns:", mass_groups.columns)

        # --- Step 4: Pre-RANSAC Refinement ---
        # This simplified function only checks for well-spaced points.
        print("\n[Step 4] Refining homologous groups before RANSAC...")
        refined_groups = mz_group_refinement(
            mass_groups,
            min_valid_points=min_valid_points,
        )
        if refined_groups.empty:
            print("[PIPELINE INFO] No groups remained after pre-RANSAC refinement.")
            return pd.DataFrame()
        print("refined groups columns:", refined_groups.columns)
        # --- Step 5: Run RANSAC Trend Analysis ---
        print("\n[Step 5] Running RANSAC trend analysis on refined groups...")
        average_ccs = refined_groups["CCS"].mean()
        actual_ransac_threshold = average_ccs * ransac_threshold_percentage
        print(
            f"[INFO] Dynamic RANSAC threshold calculated as: {actual_ransac_threshold:.2f}"
        )

        SLOPE_VALIDATOR.set_range(slope_range[0], slope_range[1])

        # Let RANSAC find all possible trends; we will filter them robustly in the next step.
        ransac_results_df = process_all_groups(
            df=refined_groups,
            group_id_col="GroupID",
            x_col="m/z",
            y_col="CCS",
            residual_threshold=actual_ransac_threshold,
            min_trend_samples=0,  # Disable filtering here; handled in validation
            min_r_squared=0.0,  # Disable filtering here; handled in validation
        )

        # --- Step 6: Post-RANSAC Validation ---
        # The new, dedicated function applies all the final quality checks.
        final_df = validate_ransac_trends(
            ransac_df=ransac_results_df,
            min_well_spaced_points=min_valid_points,  # min_valid_points now applies to the final trends
            min_library_points=min_library_points,
        )
        print("final_df columns:", final_df.columns)
        print("\n====== PIPELINE FINISHED SUCCESSFULLY ======")
        return final_df

    except FileNotFoundError as e:
        print(f"[PIPELINE ERROR] Could not find an input file: {e.filename}")
        return None
    except Exception as e:
        print(f"[PIPELINE ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()  # Print full error details for debugging
        return None
