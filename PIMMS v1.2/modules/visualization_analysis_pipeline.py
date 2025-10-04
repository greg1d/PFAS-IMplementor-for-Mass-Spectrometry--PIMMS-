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


def run_analysis_pipeline(
    experimental_filepath,
    library_filepath,
    selected_repeating_units,
    mass_error_ppm,
    min_valid_points,
    min_library_points,
    ransac_threshold_percentage,
    min_ransac_samples,
    slope_range=(0.05, 0.25),
    # min_r_squared is no longer a direct parameter here, as it's fixed in validation
):
    """
    Orchestrates the entire analysis workflow from file loading to RANSAC,
    including all validation parameters.
    """
    print("\n==============================================")
    print("====== RUNNING FULL ANALYSIS PIPELINE ======")
    print("==============================================")

    try:
        # --- Step 1 & 2: Load and Stack Data ---
        print("\n[Step 1 & 2] Loading and stacking data...")
        experimental_data_df = pd.read_csv(experimental_filepath)
        library_data_df = pd.read_csv(library_filepath)
        stacked_df = stack_library_with_adjusted(experimental_data_df, library_data_df)
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

        print("\n====== PIPELINE FINISHED SUCCESSFULLY ======")
        return final_df

    except FileNotFoundError as e:
        print(f"[PIPELINE ERROR] Could not find an input file: {e.filename}")
        return None
    except Exception as e:
        print(f"[PIPELINE ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()  # Print full error details for debugging
        return None
