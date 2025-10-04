import pandas as pd

# A comprehensive list of all possible metadata columns generated throughout the pipeline.
# The functions will ignore any columns from this list that aren't in the specific DataFrame.
METADATA_COLUMNS = [
    "Match",
    "Match Source",
    "Classification Type",
    "ID",
    "RT",
    "DT",
    "CCS",
    "m/z",
    "Mass Error (ppm)",
    "CCS Error (%)",
    "RT Error (abs)",
]


def detection_frequency_calculation(df):
    """
    Calculates the detection frequency for each feature (row) across all samples.

    Detection frequency is the percentage of samples where the feature's
    abundance is greater than zero.

    Args:
        df (pd.DataFrame): The input DataFrame, containing metadata and sample
                           abundance columns.

    Returns:
        pd.DataFrame: The DataFrame with a new 'Detection Frequency (%)' column.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    df_out = df.copy()

    # Identify abundance columns by excluding known metadata columns
    abundance_columns = [col for col in df_out.columns if col not in METADATA_COLUMNS]

    if not abundance_columns:
        print(
            "[WARNING] No abundance columns found for frequency calculation. Returning original DataFrame."
        )
        return df

    print(
        f"[INFO] Calculating detection frequency across {len(abundance_columns)} sample columns."
    )

    # Select only the abundance data
    abundance_df = df_out[abundance_columns]

    # Count detections (values > 0) for each row
    detections = (abundance_df > 0).sum(axis=1)

    # Calculate frequency as a percentage
    total_samples = len(abundance_columns)
    df_out["Detection Frequency (%)"] = (detections / total_samples) * 100

    return df_out


def average_abundance(df):
    """
    Calculates the average abundance for each feature (row) across all samples.

    The average is calculated including zeros, but ignoring NaNs.

    Args:
        df (pd.DataFrame): The input DataFrame, containing metadata and sample
                           abundance columns.

    Returns:
        pd.DataFrame: The DataFrame with a new 'Average Abundance' column.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    df_out = df.copy()

    # Identify abundance columns by excluding known metadata columns
    abundance_columns = [col for col in df_out.columns if col not in METADATA_COLUMNS]

    if not abundance_columns:
        print(
            "[WARNING] No abundance columns found for average abundance calculation. Returning original DataFrame."
        )
        return df

    print(
        f"[INFO] Calculating average abundance across {len(abundance_columns)} sample columns."
    )

    # Calculate the mean across the abundance columns for each row
    # .mean(axis=1) automatically handles NaNs by default (skipna=True)
    df_out["Average Abundance"] = df_out[abundance_columns].mean(axis=1)

    return df_out


def main():
    print(
        "This module provides functions for calculating detection frequency and average abundance."
    )
    adjusted_df = pd.read_csv("PIMMS v1.2/import folder/Dummy test output.csv")
    print("Original DataFrame:")
    print(adjusted_df.head())
    adjusted_df = detection_frequency_calculation(adjusted_df)
    adjusted_df = average_abundance(adjusted_df)
    print(adjusted_df.head())


if __name__ == "__main__":
    main()
