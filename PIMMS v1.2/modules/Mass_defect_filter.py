import pandas as pd


def mass_defect_filter(adjusted_df):
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
    filtered_df = adjusted_df[
        (adjusted_df["mass_defect"] >= -0.11) & (adjusted_df["mass_defect"] <= 0.12)
    ].copy()

    # Drop the helper column
    filtered_df.drop(columns=["mass_defect"], inplace=True)

    return filtered_df


def main():
    # Example adjusted_df with rows to process
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.666, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 10.79, 175.79, 175.79, 175.79],
            "m/z": [100.1, 100.05, 199.9, 300.3, 400.12],  # Example values
            "148 B2 16632.d.DeMP": [10, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [20, 20, 10, 10, 10],
        }
    )

    print("\n[INFO] Original adjusted_df:")
    print(adjusted_df)

    # Apply the mass filter
    filtered_df = mass_defect_filter(adjusted_df)

    print("\n[INFO] Filtered adjusted_df:")
    print(filtered_df)


if __name__ == "__main__":
    main()
