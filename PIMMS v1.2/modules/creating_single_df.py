import pandas as pd


def stack_library_with_adjusted(adjusted_df, pfas_library):
    """
    Standardizes and combines rows, now dynamically preserving all sample columns
    from the experimental data (adjusted_df).
    """
    adjusted_copy = adjusted_df.copy()
    library_copy = pfas_library.copy()

    # --- Step 1: Dynamically identify the sample columns ---
    # Define all known, non-sample columns that might be in the experimental file.
    known_non_sample_cols = {
        "Match",
        "Name",
        "Classification Type",
        "CCS",
        "RT",
        "m/z",
        "ID",
        "Average Abundance",
        "Detection Frequency (%)",
        "Match Source",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (abs)",
        "DT",
    }
    # Any column NOT in this set is considered a sample column.
    sample_cols = sorted(
        [col for col in adjusted_df.columns if col not in known_non_sample_cols]
    )
    if sample_cols:
        print(f"[INFO] Identified and will preserve sample columns: {sample_cols}")

    # --- Step 2: Prepare and stack the dataframes ---
    if "Match" in adjusted_copy.columns:
        adjusted_copy.rename(columns={"Match": "Name"}, inplace=True)
    else:
        print(
            "\n[WARNING] 'Match' column not found in adjusted_df. No column was renamed."
        )

    library_copy["Classification Type"] = "External Standard"

    # `pd.concat` correctly preserves all unique columns from both dataframes
    stacked_df = pd.concat([adjusted_copy, library_copy], ignore_index=True, sort=False)
    stacked_df = stacked_df.fillna(0)

    # --- Step 3: Create the final list of columns to keep ---
    # This combines the essential columns with your dynamic sample columns.
    base_columns_to_keep = [
        "Name",
        "Classification Type",
        "CCS",
        "RT",
        "m/z",
        "ID",
        "Average Abundance",
        "Detection Frequency (%)",
    ]
    final_columns_to_keep = base_columns_to_keep + sample_cols

    # --- Step 4: Filter the DataFrame, preserving all desired columns ---
    # This ensures we only try to select columns that actually exist in the stacked_df
    existing_cols = [col for col in final_columns_to_keep if col in stacked_df.columns]

    return stacked_df[existing_cols]


def main():
    library_df = pd.read_csv(
        "PIMMS v1.2\import folder\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    )
    adjusted_df = pd.read_csv("PIMMS v1.2\data\SealsPIMMS.csv")

    combined_df = stack_library_with_adjusted(adjusted_df, library_df)
    combined_df.to_csv("PIMMS v1.2\data\stacked_output.csv")


if __name__ == "__main__":
    main()
