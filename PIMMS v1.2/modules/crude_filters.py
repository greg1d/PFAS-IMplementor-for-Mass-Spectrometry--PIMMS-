from blank_subtraction import count_non_zero_rows


def apply_min_intensity_filter(df, min_intensity=100):
    """
    Sets values below the minimum intensity threshold in '.d' columns to 0.
    Keeps all rows intact.

    Args:
        df (pd.DataFrame): DataFrame containing the dataset.
        min_intensity (float): Minimum intensity threshold.

    Returns:
        pd.DataFrame: Modified DataFrame with intensity values below the threshold set to 0.
    """
    d_columns = [col for col in df.columns if ".d" in col]
    if not d_columns:
        raise ValueError("No '.d' columns found for intensity filtering.")

    # Apply the intensity threshold: set values below the threshold to 0
    df[d_columns] = df[d_columns].applymap(lambda x: x if x >= min_intensity else 0)

    print(f"[INFO] Intensity filter applied: values below {min_intensity} set to 0.")
    return df


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
    # Adjust the column name to match the actual column in your dataset
    column_name = "m/z" if "m/z" in df.columns else "Experimental m/z"

    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the DataFrame.")

    filtered_df = df[(df[column_name] >= mass_min) & (df[column_name] <= mass_max)]
    print(f"[INFO] After mass filter: {filtered_df.shape[0]} rows remain.")
    return filtered_df


def process_with_filters(
    df, min_intensity=100, rt_min=1.0, rt_max=10.0, mass_min=50.0, mass_max=500.0
):
    """
    Applies intensity, RT, and mass filters to the dataset, then counts non-zero rows.

    Args:
        df (pd.DataFrame): Input DataFrame.
        min_intensity (float): Minimum intensity threshold for the intensity filter.
        rt_min (float): Minimum RT threshold.
        rt_max (float): Maximum RT threshold.
        mass_min (float): Minimum mass threshold.
        mass_max (float): Maximum mass threshold.

    Returns:
        pd.DataFrame: Filtered DataFrame after applying all filters.
        tuple: Group average and standard deviation of non-zero rows after filters.
    """
    print("[INFO] Starting filtering process...")

    # Apply intensity filter
    df = apply_min_intensity_filter(df, min_intensity)

    # Apply RT filter
    df = apply_rt_filter(df, rt_min=rt_min, rt_max=rt_max)

    # Apply mass filter
    df = apply_mass_filter(df, mass_min=mass_min, mass_max=mass_max)

    # Recalculate non-zero rows
    group_avg, group_std = count_non_zero_rows(df)

    print(
        f"[INFO] After all filters:\n"
        f"  Average Non-Zero Rows: {group_avg:.2f}\n"
        f"  Std Dev of Non-Zero Rows: {group_std:.2f}"
    )

    return df, group_avg, group_std
