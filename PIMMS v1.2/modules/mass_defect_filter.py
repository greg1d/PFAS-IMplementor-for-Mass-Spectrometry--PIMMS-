def mass_defect_filter(
    experimental_df,
    lower_mass_filter_bound=-0.11,
    upper_mass_filter_bound=0.12,
):
    """
    [MODIFIED] Filters a single DataFrame based on mass defect.
    Handles empty inputs gracefully.

    Args:
        experimental_df (pd.DataFrame): Input DataFrame with a mass column.
        mz_col (str): Name of the mass-to-charge ratio column to filter on.
        lower_mass_filter_bound (float): The lower bound for the mass defect.
        upper_mass_filter_bound (float): The upper bound for the mass defect.

    Returns:
        pd.DataFrame: A new, filtered DataFrame.
    """
    # --- FIX 1: Guard Clause for empty DataFrame ---
    if experimental_df.empty:
        print("[INFO] Input DataFrame is empty. Skipping mass defect filter.")
        return experimental_df

    initial_rows = len(experimental_df)

    # Use a temporary copy to avoid SettingWithCopyWarning
    df_copy = experimental_df.copy()

    # Compute the deviation from the nearest integer
    df_copy["mass_defect"] = df_copy["m/z"] - df_copy["m/z"].round()

    # Filter rows where the deviation is within the specified bounds
    filtered_df = df_copy[
        (df_copy["mass_defect"] >= lower_mass_filter_bound)
        & (df_copy["mass_defect"] <= upper_mass_filter_bound)
    ].copy()

    # Drop the helper column and reset the index
    filtered_df.drop(columns=["mass_defect"], inplace=True)
    filtered_df.reset_index(drop=True, inplace=True)

    final_rows = len(filtered_df)
    rows_removed = initial_rows - final_rows
    print(
        f"✔️ Mass defect filter applied. Removed {rows_removed} rows. {final_rows} rows remain."
    )

    return filtered_df
