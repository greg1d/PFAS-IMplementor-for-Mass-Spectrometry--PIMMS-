import pandas as pd
import os


def process_lipid_data(df):
    """
    Adds 'M-H-' and 'Mass_Defect_from_Integer' columns to a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame, must contain a 'Monoiso_Mass' column.

    Returns:
        pd.DataFrame: A new DataFrame with the added columns, or None on error.
    """
    df_processed = df.copy()

    # --- 1. Calculate 'M-H-' column ---
    source_col = "Monoiso_Mass"
    new_mh_col = "M-H-"
    proton_mass = 1.0078246

    if source_col not in df_processed.columns:
        print(f"[ERROR] Required source column '{source_col}' not found.")
        return None

    # Ensure the source column is numeric, converting non-numeric values to NaN
    df_processed[source_col] = pd.to_numeric(df_processed[source_col], errors="coerce")

    # Perform the subtraction
    df_processed[new_mh_col] = df_processed[source_col] - proton_mass

    # --- 2. Calculate Mass Defect from the new 'M-H-' column ---
    defect_col_name = "Mass_Defect_from_Integer"

    # This calculation is vectorized for efficiency
    original_values = df_processed[new_mh_col]
    rounded_values = original_values.round(0)

    df_processed[defect_col_name] = original_values - rounded_values

    return df_processed


def main():
    """
    Main function to run the data processing workflow.
    """
    # --- Configuration ---
    INPUT_FILE_PATH = r"PIMMS v1.2\testing_expanded_library\pfas_processed.csv"
    OUTPUT_FILE_PATH = (
        r"PIMMS v1.2\testing_expanded_library\pfas_processed_with_mass_defect.csv"
    )
    # -------------------

    try:
        if not os.path.exists(INPUT_FILE_PATH):
            raise FileNotFoundError(f"Input file not found at: {INPUT_FILE_PATH}")

        print(f"Loading data from '{os.path.basename(INPUT_FILE_PATH)}'...")
        input_df = pd.read_csv(INPUT_FILE_PATH)

        print("Processing data...")
        processed_df = process_lipid_data(input_df)

        if processed_df is not None:
            print("\nProcessing complete. Showing first 5 results of new columns:")
            print(
                processed_df[["Monoiso_Mass", "M-H-", "Mass_Defect_from_Integer"]]
                .head()
                .to_string()
            )

            print(f"\nSaving updated data to '{os.path.basename(OUTPUT_FILE_PATH)}'...")
            processed_df.to_csv(OUTPUT_FILE_PATH, index=False)
            print("Done.")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
