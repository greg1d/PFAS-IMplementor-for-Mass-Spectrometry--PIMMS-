import pandas as pd


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


def main():
    """
    Main function for testing the fluorinated_density_filter function with a sample DataFrame.
    """
    # Create a sample DataFrame for testing
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5, 6],
            "RT": [3.4, 3.4, 3.665, 3.666, 3.664, 3.7],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319, 23.500],
            "CCS": [120, 300.79, 300.0, 300.0, 300.0, 10.0],
            "m/z": [98, 100, 200, 300, 400, 500],
            "148 B2 16632.d.DeMP": [10000, 10, 10000, 10, 10000, 10],
            "149 B2 16631.d.DeMP": [10, 10, 10, 10, 10, 10],
        }
    )

    # Apply the fluorinated density filter
    filtered_df = fluorinated_density_filter(adjusted_df)

    # Print the filtered DataFrame
    print(filtered_df)


if __name__ == "__main__":
    main()
