import pandas as pd


def stack_library_with_adjusted(adjusted_df, pfas_library):
    """
    Standardizes and combines rows from adjusted_df and pfas_library.
    1. Renames the 'Match' column to 'Name' in the adjusted_df.
    2. Adds a 'Match Source' column to the pfas_library.

    Returns:
        pd.DataFrame: The combined dataset.
    """
    # It's best practice to work on copies to avoid changing the original DataFrames
    # outside of this function (this prevents unintended side effects).
    adjusted_copy = adjusted_df.copy()
    library_copy = pfas_library.copy()

    # --- Task 1: Rename 'Match' to 'Name' in the adjusted DataFrame ---
    # We check if the 'Match' column exists first to prevent errors.
    if "Match" in adjusted_copy.columns:
        adjusted_copy.rename(columns={"Match": "Name"}, inplace=True)
    else:
        print(
            "\n[WARNING] 'Match' column not found in adjusted_df. No column was renamed."
        )

    # --- Task 2: Add and fill 'Match Source' column in the library DataFrame ---
    library_copy["Classification Type"] = "External Standard"

    # ✅ Stack the two MODIFIED DataFrames
    stacked_df = pd.concat([adjusted_copy, library_copy], ignore_index=True)

    # Be aware: .fillna(0) will replace empty text (like a missing 'Name') with the number 0.
    # A more advanced approach might involve filling text columns with '' and numeric columns with 0.
    stacked_df = stacked_df.fillna(0)

    # ✅ Drop additional error-related columns if they exist
    columns_to_keep = [
        "Name",
        "Classification Type",
        "CCS",
        "RT",
        "m/z",
        "ID",
        "Average Abundance",
        "Detection Frequency (%)",
    ]
    stacked_df = stacked_df[columns_to_keep]
    final_columns = [col for col in columns_to_keep if col in stacked_df.columns]
    stacked_df = stacked_df[final_columns]

    return stacked_df


def main():
    library_df = pd.read_csv(
        "PIMMS v1.2\import folder\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    )
    adjusted_df = pd.read_csv("PIMMS v1.2\data\SealsPIMMS.csv")

    combined_df = stack_library_with_adjusted(adjusted_df, library_df)
    combined_df.to_csv("PIMMS v1.2\data\stacked_output.csv")


if __name__ == "__main__":
    main()
