def apply_min_intensity_filter(df, min_intensity=100):
    """
    Filters rows where all '.d' columns have intensity values below the minimum threshold.

    Args:
        df (pd.DataFrame): DataFrame containing the dataset.
        min_intensity (float): Minimum intensity threshold.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    d_columns = [col for col in df.columns if ".d" in col]
    if not d_columns:
        raise ValueError("No '.d' columns found for intensity filtering.")

    # Filter rows based on the maximum value across `.d` columns
    filtered_df = df[df[d_columns].max(axis=1) >= min_intensity]
    print(f"[INFO] After intensity filter: {filtered_df.shape[0]} rows remain.")
    return filtered_df


def apply_rt_filter(df, rt_min=1.0, rt_max=10.0):
    """
    Filters rows based on retention time (RT).

    Args:
        df (pd.DataFrame): DataFrame containing the dataset.
        rt_min (float): Minimum RT threshold.
        rt_max (float): Maximum RT threshold.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if "RT" not in df.columns:
        raise ValueError("Column 'RT' not found in the DataFrame.")

    filtered_df = df[(df["RT"] >= rt_min) & (df["RT"] <= rt_max)]
    print(f"[INFO] After RT filter: {filtered_df.shape[0]} rows remain.")
    return filtered_df


def apply_mass_filter(df, mass_min=50.0, mass_max=500.0):
    """
    Filters rows based on mass.

    Args:
        df (pd.DataFrame): DataFrame containing the dataset.
        mass_min (float): Minimum mass threshold.
        mass_max (float): Maximum mass threshold.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if "Experimental m/z" not in df.columns:
        raise ValueError("Column 'Experimental m/z' not found in the DataFrame.")

    filtered_df = df[
        (df["Experimental m/z"] >= mass_min) & (df["Experimental m/z"] <= mass_max)
    ]
    print(f"[INFO] After mass filter: {filtered_df.shape[0]} rows remain.")
    return filtered_df
