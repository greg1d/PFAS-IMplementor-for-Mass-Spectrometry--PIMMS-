def fluorinated_density_filter(adjusted_df):
    """
    Filters rows from the adjusted DataFrame based on a fluorinated compound density model.
    A row is removed if its CCS value exceeds the threshold defined by:
        CCS < (m/z * 0.19) + 110.28

    Args:
        adjusted_df (pd.DataFrame): The adjusted DataFrame containing 'm/z' and 'CCS' columns.

    Returns:
        pd.DataFrame: Filtered DataFrame with non-conforming rows removed.
    """
    filtered_df = adjusted_df[
        adjusted_df.apply(lambda row: row["m/z"] * 0.19 + 110.28 > row["CCS"], axis=1)
    ]
    return filtered_df
