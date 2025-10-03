import pandas as pd

from .ccsvmz_analysis import process_all_groups

# Import all the necessary analysis modules
from .repeat_unit_analysis import (
    mz_group_refinement,
    mz_repeating_unit_analysis,
    stack_library_with_adjusted,
)


# --- THIS IS THE CORRECTED FUNCTION DEFINITION ---
def run_analysis_pipeline(
    experimental_filepath,  # <-- Takes a file path
    library_filepath,  # <-- Takes a file path
    selected_repeating_units,  # <-- Has the correct parameter name
    mass_error_ppm,
    min_valid_points,
    min_library_points,
    ransac_threshold,
    min_ransac_samples,
):
    """
    Orchestrates the entire analysis workflow from file loading to RANSAC.
    """
    print("\n==============================================")
    print("====== RUNNING FULL ANALYSIS PIPELINE ======")
    print("==============================================")

    try:
        # --- Step 1: Load Data ---
        print("\n[Step 1] Loading data...")
        experimental_data_df = pd.read_csv(experimental_filepath)
        library_data_df = pd.read_csv(library_filepath)

        # --- Step 2: Stack and Standardize ---
        print("\n[Step 2] Stacking and standardizing dataframes...")
        stacked_df = stack_library_with_adjusted(experimental_data_df, library_data_df)
        if stacked_df is None or stacked_df.empty:
            raise ValueError("Data stacking resulted in an empty DataFrame.")

        # --- Step 3: Find Homologous Series ---
        print("\n[Step 3] Finding homologous series...")
        mass_groups = mz_repeating_unit_analysis(
            stacked_df,
            selected_repeating_units,
            mass_error_ppm=mass_error_ppm,
            min_valid_points=min_valid_points,
        )
        if mass_groups.empty:
            print("[PIPELINE INFO] No initial homologous groups were found.")
            return pd.DataFrame()

        # --- Step 4: Refine Groups ---
        print("\n[Step 4] Refining found groups...")
        refined_groups = mz_group_refinement(
            mass_groups,
            min_library_points=min_library_points,
            min_valid_points=min_valid_points,
        )
        if refined_groups.empty:
            print("[PIPELIPELINE INFO] No groups remained after refinement.")
            return pd.DataFrame()

        # --- Step 5: Run RANSAC Trend Analysis ---
        print("\n[Step 5] Running RANSAC trend analysis on refined groups...")
        final_df = process_all_groups(
            df=refined_groups,
            group_id_col="GroupID",
            x_col="m/z",
            y_col="CCS",
            residual_threshold=ransac_threshold,
            min_trend_samples=min_ransac_samples,
        )

        print("\n====== PIPELINE FINISHED SUCCESSFULLY ======")
        return final_df

    except FileNotFoundError as e:
        print(f"[PIPELINE ERROR] Could not find an input file: {e.filename}")
        return None
    except Exception as e:
        print(f"[PIPELINE ERROR] An unexpected error occurred: {e}")
        return None
