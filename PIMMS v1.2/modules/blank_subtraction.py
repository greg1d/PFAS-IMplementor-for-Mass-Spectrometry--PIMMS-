import os
import pandas as pd


def read_and_filter_csv(file_path):
    """
    Reads a CSV file, selects the first 5 columns and any column containing '.d',
    and adds a column for the source file.
    """
    print(f"Reading file: {file_path}...")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Load the CSV file with low_memory=False to handle mixed types
        df = pd.read_csv(file_path, low_memory=False)

        # Select the first 5 columns by index and any column containing '.d'
        selected_columns = list(df.columns[:5]) + [
            col for col in df.columns if ".d" in col
        ]
        filtered_df = df[selected_columns]

        return filtered_df
    except Exception as e:
        raise RuntimeError(f"Error processing {file_path}: {e}")


def blank_subtraction(control_df, experimental_df):
    """
    Perform blank subtraction by averaging control samples and subtracting
    the averaged values from the experimental samples. Also calculates the
    standard deviation of control samples row-wise.

    Parameters:
        control_df (pd.DataFrame): DataFrame containing control samples.
        experimental_df (pd.DataFrame): DataFrame containing experimental samples.

    Returns:
        pd.DataFrame: Experimental DataFrame with blanks subtracted.
        pd.Series: Row-wise means of the control samples.
        pd.Series: Row-wise standard deviations of the control samples.
    """
    if len(control_df) != len(experimental_df):
        raise ValueError(
            "Control and experimental DataFrames must have the same number of rows."
        )

    # Compute the average and standard deviation of the control columns row-wise
    control_mean = control_df.mean(axis=1)
    control_std = control_df.std(axis=1)

    # Subtract the averaged control values from each experimental column
    subtracted_df = experimental_df.copy()
    for column in experimental_df.columns:
        subtracted_df[column] = experimental_df[column] - control_mean

    # Ensure no negative values
    subtracted_df = subtracted_df.clip(lower=0)

    return subtracted_df, control_mean, control_std
