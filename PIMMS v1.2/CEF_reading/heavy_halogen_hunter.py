import pandas as pd
import numpy as np
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    compute_kaufman_constants,
    get_cef_sample_names,
    run_matching_pipeline,
)
from calculating_Kaufman_parameters_file_2 import align_features, create_summary_table

# --- Data Extraction, Matching, and Alignment Functions (from previous steps) ---
# For brevity, the full code of these functions is collapsed.
# Ensure they are present in your script as defined in the previous responses.


def heavy_halogen_hunter(df):
    """
    Checks each row for an M+2 isotopic signature characteristic of Cl or Br,
    and adds a column with the raw M+2/M isotopic ratio.
    This version uses np.select for efficient, vectorized operation.

    Args:
        df (pd.DataFrame): DataFrame containing 'Intensity_1' and 'Intensity_3'.

    Returns:
        pd.DataFrame: The input DataFrame with new 'M/M+2 Distribution' and 'Heavy_Halogen' columns.
    """
    # --- NEW: Calculate the ratio and add it as a new column ---
    # Initialize the new column with NaN (Not a Number)
    df["M/M+2 Distribution"] = np.nan

    # Create a mask for rows where division is safe (Intensity_1 > 0)
    safe_division_mask = df["Intensity_1"] > 0

    # Calculate the ratio only for the safe rows and fill the new column
    df.loc[safe_division_mask, "M/M+2 Distribution"] = (
        df.loc[safe_division_mask, "Intensity_3"]
        / df.loc[safe_division_mask, "Intensity_1"]
    )
    # --- End of New Code ---

    # Define the conditions in order of priority, now using the new ratio column
    conditions = [
        df["M/M+2 Distribution"] > 0.28,
        (df["Intensity_3"] == 0) | (df["Intensity_3"].isna()),
    ]

    # Define the choices corresponding to each condition
    choices = [
        "Potential Cl, Br present",
        "No M+2 peak detected - insufficient signal",
    ]

    # The default value if no conditions are met
    default_choice = "No Cl or Br isotopic pattern detected"

    # Create the 'Isotopic_analysis' classification column using np.select
    df["Isotopic_analysis"] = np.select(conditions, choices, default=default_choice)

    return df


def main():
    """Main function to run the full workflow."""
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    # Load Data
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = pimms_df.columns.str.strip()
    all_cef_data = parse_all_cef_files_in_folder(cef_folder)

    # Pre-calculate Kaufman Constants (now includes Intensity_3)
    kaufman_df = compute_kaufman_constants(all_cef_data)

    # Run Matching and Alignment Pipeline
    sample_names = get_cef_sample_names(cef_folder)
    combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)

    if combined_df.empty:
        print("\n--- No matches were found, skipping alignment. ---")
        return

    aligned_df = align_features(combined_df)

    # Merge Kaufman data with Aligned Features
    final_long_df = pd.merge(
        aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
    )

    # Create the final summary table
    summary_table = create_summary_table(final_long_df)

    summary_table = heavy_halogen_hunter(summary_table)
    print(summary_table)
    summary_table.to_csv(
        "PIMMS v1.2/CEF_reading/summary_with_isotopic_analysis.csv", index=False
    )


if __name__ == "__main__":
    main()
