def smearing_filter(adjusted_df, rt_tolerance=0.5, ccs_tolerance=2):
    """
    Filters rows from the adjusted DataFrame to eliminate mass shift rows based on tolerances.
    If a peak is significantly stronger in a `.d` column, the weaker peak is set to 0 in that column.

    Args:
        adjusted_df (pd.DataFrame): The adjusted DataFrame containing intensity and metadata columns.
        rt_tolerance (float): Retention time tolerance.
        ccs_tolerance (float): Tolerance for CCS as a percentage.

    Returns:
        pd.DataFrame: Filtered DataFrame where weaker intensities are zeroed out in relevant `.d` columns.
    """
    # Identify intensity columns containing ".d"
    intensity_columns = [col for col in adjusted_df.columns if ".d" in col]
    if not intensity_columns:
        raise ValueError("No intensity columns found in the DataFrame.")

    # Sort DataFrame by Experimental m/z and reset index
    adjusted_df = adjusted_df.sort_values("m/z").reset_index(drop=True)

    # Iterate through rows to find and eliminate weaker intensity values
    for i in range(len(adjusted_df)):
        mz1 = adjusted_df.loc[i, "m/z"]
        ccs1 = adjusted_df.loc[i, "CCS"]
        retention_time1 = adjusted_df.loc[i, "RT"]

        # Get potential matches with a **lower mass (-2 Da cutoff)** but within tolerances
        potential_matches = adjusted_df[
            (adjusted_df["m/z"] >= mz1 - 2)
            & (adjusted_df["m/z"] < mz1)
            & (abs(adjusted_df["CCS"] - ccs1) / ccs1 * 100 < ccs_tolerance)
            & (abs(adjusted_df["RT"] - retention_time1) <= rt_tolerance)
        ]

        for j in potential_matches.index:
            if j >= i:
                continue

            # Compare each intensity column separately
            for col in intensity_columns:
                int1 = adjusted_df.at[i, col]
                int2 = adjusted_df.at[j, col]

                # If the intensity of peak j (lower mass) is much stronger, zero out peak i in that column
                if int2 > 50 * int1:
                    adjusted_df.at[i, col] = 0

    return adjusted_df
