import pandas as pd


def detection_frequency_filter(adjusted_df, frequency_threshold):
    """
    Removes rows where the detection frequency across all `.d` intensity columns is below a defined threshold.

    Args:
        adjusted_df (pd.DataFrame): The adjusted DataFrame containing intensity and metadata columns.
        frequency_threshold (float): The minimum proportion of nonzero values required for a row to be kept (default 10%).

    Returns:
        pd.DataFrame: Filtered DataFrame with low-detection rows removed.
    """
    # Identify intensity columns containing ".d"
    intensity_columns = [col for col in adjusted_df.columns if ".d" in col]
    if not intensity_columns:
        raise ValueError("No intensity columns found in the DataFrame.")

    # Count the number of nonzero values per row in intensity columns
    detection_counts = (adjusted_df[intensity_columns] > 0).sum(axis=1)
    total_columns = len(intensity_columns)
    detection_frequencies = detection_counts / total_columns

    # Apply the frequency threshold filter
    adjusted_df = adjusted_df[detection_frequencies >= (frequency_threshold / 100)]

    return adjusted_df


def main():
    # Example adjusted_df with rows to process
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.666, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 176.79, 175.79, 175.79, 175.79],
            "m/z": [100, 100.00012, 200, 300, 400],
            "148 B2 16632.d.DeMP": [0, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [1, 20, 10, 10, 10],
        }
    )

    frequency_threshold = 10

    adjusted_df = detection_frequency_filter(adjusted_df, frequency_threshold)

    print("\n[INFO] Updated adjusted_df after merging groups:")
    print(adjusted_df)


if __name__ == "__main__":
    main()
