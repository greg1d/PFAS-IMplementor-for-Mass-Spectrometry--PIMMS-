def detection_frequency_filter(experimental_df, metadata_cols, frequency_threshold):
    """
    Removes features (rows) based on their detection frequency across samples.

    The frequency is calculated only on the sample columns, which are identified
    by excluding the provided metadata columns.

    Args:
        experimental_df (pd.DataFrame): DataFrame containing metadata and sample values.
        metadata_cols (list): A list of metadata column names to be excluded from the calculation.
        frequency_threshold (float): The minimum detection frequency required for a row to be
                                     kept, expressed as a percentage (e.g., 50 for 50%).

    Returns:
        pd.DataFrame: A new DataFrame with low-frequency rows removed.
    """
    # --- 1. Identify Sample Columns ---
    # This robustly finds sample columns by excluding metadata, replacing the ".d" search.
    sample_cols = [col for col in experimental_df.columns if col not in metadata_cols]

    if not sample_cols:
        print("[WARNING] No sample columns found for frequency filtering.")
        return experimental_df

    print(f"Calculating detection frequency across columns: {sample_cols}")

    # --- 2. Calculate Detection Frequency ---
    # Count the number of non-zero values per row ONLY in the sample columns
    detection_counts = (experimental_df[sample_cols] > 0).sum(axis=1)
    total_samples = len(sample_cols)
    detection_frequencies = detection_counts / total_samples

    # --- 3. Apply the Filter ---
    # Convert the user-provided percentage to a proportion (e.g., 50 -> 0.5)
    required_frequency = frequency_threshold / 100

    # Keep rows where the calculated frequency is >= the required frequency
    filtered_df = experimental_df[
        detection_frequencies >= required_frequency
    ].reset_index(drop=True)

    return filtered_df
