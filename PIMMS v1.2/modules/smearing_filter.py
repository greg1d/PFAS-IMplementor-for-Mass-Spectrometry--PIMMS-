def smearing_filter(
    experimental_df,
    mz_col="m/z",
    rt_col="RT",
    ccs_col="CCS",
    rt_tolerance=0.5,
    ccs_tolerance=2,
):
    """
    Filters out artifact peaks caused by smearing or isotopes.

    For each peak, it looks for a nearby peak with a slightly lower mass. If that
    lower-mass peak is significantly stronger (50x) in a given sample, the
    intensity of the higher-mass peak is set to 0 for that sample.

    Args:
        experimental_df (pd.DataFrame): DataFrame with metadata and experimental samples.
        metadata_cols (list): List of metadata column names.
        mz_col (str): Name of the mass-to-charge ratio column.
        rt_col (str): Name of the retention time column.
        ccs_col (str): Name of the collisional cross-section column.
        rt_tolerance (float): Retention time tolerance for matching peaks.
        ccs_tolerance (float): CCS tolerance percentage for matching peaks.

    Returns:
        pd.DataFrame: A new DataFrame with smearing artifacts zeroed out.
    """
    # --- 1. Setup and Validation ---
    # Create a copy to avoid modifying the original DataFrame
    if experimental_df.empty:
        print("[INFO] Input DataFrame is empty. Skipping smearing filter.")
        return experimental_df

    df_filtered = experimental_df.copy()

    # Dynamically identify sample columns by excluding metadata
    sample_cols = [col for col in df_filtered.columns]

    # Check if required metadata columns exist
    required_cols = [mz_col, rt_col, ccs_col]
    for col in required_cols:
        if col not in df_filtered.columns:
            raise ValueError(f"Required column '{col}' not found in the DataFrame.")

    if not sample_cols:
        print("[WARNING] No sample columns found for smearing filter.")
        return df_filtered

    print(f"Applying smearing filter to sample columns: {sample_cols}")

    # Sort by m/z for efficient searching, and reset index
    df_sorted = df_filtered.sort_values(mz_col).reset_index(drop=True)

    # --- 2. Core Filtering Logic ---
    # Iterate through each row (peak)
    for i in range(len(df_sorted)):
        mz1 = df_sorted.loc[i, mz_col]
        ccs1 = df_sorted.loc[i, ccs_col]
        rt1 = df_sorted.loc[i, rt_col]

        # Find potential artifact sources: peaks with a slightly lower mass but within RT and CCS tolerance
        potential_matches = df_sorted[
            (df_sorted[mz_col] >= mz1 - 2)
            & (df_sorted[mz_col] < mz1)
            & (abs(df_sorted[ccs_col] - ccs1) / ccs1 * 100 < ccs_tolerance)
            & (abs(df_sorted[rt_col] - rt1) <= rt_tolerance)
        ]

        # If matching lower-mass peaks are found, compare intensities
        if not potential_matches.empty:
            for j in potential_matches.index:
                # Compare each sample column individually
                for col in sample_cols:
                    intensity_high_mass = df_sorted.at[i, col]
                    intensity_low_mass = df_sorted.at[j, col]

                    # If the lower mass peak is >50x stronger, it's likely the source.
                    # Zero out the higher mass peak's intensity in this specific sample.
                    if intensity_low_mass > 50 * intensity_high_mass:
                        df_sorted.at[i, col] = 0

    print("✔️ Smearing filter applied.")
    return df_sorted
