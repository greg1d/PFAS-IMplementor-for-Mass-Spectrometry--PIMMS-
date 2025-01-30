def mass_defect_filter(
    adjusted_df, lower_mass_filter_bound=-0.11, upper_mass_filter_bound=0.12
):
    """
    Filters masses in the 'm/z' column that are within -0.11 to 0.12 of their nearest integer.

    Args:
        adjusted_df (pd.DataFrame): Input DataFrame with 'm/z' column.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only masses within the specified range.
    """
    if "m/z" not in adjusted_df.columns:
        raise ValueError("Column 'm/z' not found in the DataFrame.")

    # Compute the deviation from the nearest integer
    adjusted_df["mass_defect"] = adjusted_df["m/z"] - adjusted_df["m/z"].round()

    # Filter rows where the deviation is within -0.11 to 0.12
    adjusted_df = adjusted_df[
        (adjusted_df["mass_defect"] >= lower_mass_filter_bound)
        & (adjusted_df["mass_defect"] <= upper_mass_filter_bound)
    ].copy()

    # Drop the helper column
    adjusted_df.drop(columns=["mass_defect"], inplace=True)

    return adjusted_df
