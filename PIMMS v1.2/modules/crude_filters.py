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
    if experimental_df.empty:
        print("[INFO] No data available to apply intensity filter.")
        return experimental_df
    filtered_df = experimental_df.copy()

    # --- The Fix: Dynamically identify sample columns by excluding metadata ---
    # This replaces the brittle search for '.d' in column names.
    exp_sample_cols = [col for col in filtered_df.columns if col not in metadata_cols]

    if not exp_sample_cols:
        print(
            "[WARNING] No experimental sample columns found to apply intensity filter."
        )
        return filtered_df

    # Use boolean masking with .mask() for efficient filtering.
    # Where the condition (value < threshold) is True, the value is replaced with 0.
    filtered_df[exp_sample_cols] = filtered_df[exp_sample_cols].mask(
        filtered_df[exp_sample_cols] < min_intensity, 0
    )

    return filtered_df


def apply_rt_filter(experimental_df, rt_min=1.0, rt_max=10.0):
    """
    Filters rows from the experimental DataFrame based on retention time (RT).

    Args:
        experimental_df (pd.DataFrame): DataFrame containing the experimental dataset.
        rt_min (float): Minimum RT threshold (inclusive).
        rt_max (float): Maximum RT threshold (inclusive).

    Returns:
        pd.DataFrame: A new, filtered DataFrame.
    """
    if experimental_df.empty:
        print("[INFO] No data available to apply RT filter.")
        return experimental_df
    # --- 1. Validation ---
    if "RT" not in experimental_df.columns:
        raise ValueError("Required column 'RT' not found in the DataFrame.")

    print(
        f"Applying RT filter to experimental data with bounds [{rt_min}, {rt_max}]..."
    )

    # --- 2. Apply Filter ---
    filtered_df = experimental_df[
        (experimental_df["RT"] >= rt_min) & (experimental_df["RT"] <= rt_max)
    ].reset_index(drop=True)

    return filtered_df


def apply_mass_filter(experimental_df, mz_min=50.0, mz_max=500.0):
    """
    Filters rows from the experimental DataFrame based on m/z values.

    Args:
        experimental_df (pd.DataFrame): DataFrame containing the experimental dataset.
        rt_min (float): Minimum RT threshold (inclusive).
        rt_max (float): Maximum RT threshold (inclusive).

    Returns:
        pd.DataFrame: A new, filtered DataFrame.
    """
    if experimental_df.empty:
        print("[INFO] No data available to apply m/z filter.")
        return experimental_df
    # --- 1. Validation ---
    if "m/z" not in experimental_df.columns:
        raise ValueError("Required column 'm/z' not found in the DataFrame.")

    print(
        f"Applying m/z filter to experimental data with bounds [{mz_min}, {mz_max}]..."
    )

    # --- 2. Apply Filter ---
    filtered_df = experimental_df[
        (experimental_df["m/z"] >= mz_min) & (experimental_df["m/z"] <= mz_max)
    ].reset_index(drop=True)

    return filtered_df
