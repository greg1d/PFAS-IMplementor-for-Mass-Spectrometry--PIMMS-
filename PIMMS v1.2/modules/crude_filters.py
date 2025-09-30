from blank_subtraction import count_non_zero_rows


def apply_min_intensity_filter(experimental_df, metadata_cols, min_intensity=100):
    """
    Sets values below a minimum intensity threshold to 0, operating only on
    experimental sample columns.

    Args:
        experimental_df (pd.DataFrame): DataFrame containing metadata and experimental samples.
        metadata_cols (list): A list of the metadata column names, which will be excluded from filtering.
        min_intensity (float): The minimum intensity threshold.

    Returns:
        pd.DataFrame: A new DataFrame with the intensity filter applied to sample columns.
    """
    # Create a copy to ensure the original DataFrame outside the function is not modified
    filtered_df = experimental_df.copy()

    # --- The Fix: Dynamically identify sample columns by excluding metadata ---
    # This replaces the brittle search for '.d' in column names.
    exp_sample_cols = [col for col in filtered_df.columns if col not in metadata_cols]

    if not exp_sample_cols:
        print(
            "[WARNING] No experimental sample columns found to apply intensity filter."
        )
        return filtered_df

    print(f"Applying intensity filter to columns: {exp_sample_cols}")

    # Use boolean masking with .mask() for efficient filtering.
    # Where the condition (value < threshold) is True, the value is replaced with 0.
    filtered_df[exp_sample_cols] = filtered_df[exp_sample_cols].mask(
        filtered_df[exp_sample_cols] < min_intensity, 0
    )

    print(
        f"✔️ Intensity filter applied: values below {min_intensity} in sample columns set to 0."
    )
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
