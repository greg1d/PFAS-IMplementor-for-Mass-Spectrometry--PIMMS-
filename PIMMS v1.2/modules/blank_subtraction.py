import pandas as pd
import numpy as np
import os


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

        # Select the first 5 columns and any column containing '.d'
        selected_columns = list(df.columns[:5]) + [
            col for col in df.columns if ".d" in col
        ]
        filtered_df = df[selected_columns]

        return filtered_df
    except Exception as e:
        raise RuntimeError(f"Error processing {file_path}: {e}")


def separate_control_experimental(combined_data, control_columns):
    """
    Separates the combined DataFrame into control and experimental DataFrames.

    Args:
        combined_data (pd.DataFrame): The combined data containing all samples.
        control_columns (list): List of control sample column names.

    Returns:
        control_df (pd.DataFrame): DataFrame containing control samples and metadata.
        experimental_df (pd.DataFrame): DataFrame containing experimental samples.
    """
    # Ensure all control columns are present
    for col in control_columns:
        if col not in combined_data.columns:
            raise ValueError(f"Control column '{col}' not found in the data.")

    # Select control samples and metadata (first 5 columns)
    control_df = combined_data[combined_data.columns[:5].tolist() + control_columns]

    # Select experimental samples (all other '.d' columns not in control_columns)
    experimental_columns = [
        col
        for col in combined_data.columns
        if col not in control_df.columns and ".d" in col
    ]
    experimental_df = combined_data[
        combined_data.columns[:5].tolist() + experimental_columns
    ]

    return control_df, experimental_df


def method_1_blank_subtraction(control_df, experimental_df):
    """
    Basic subtraction of the control mean from experimental samples.
    """
    control_mean = control_df.iloc[:, 5:].mean(axis=1)  # Exclude first 5 columns
    adjusted_df = experimental_df.iloc[:, 5:].sub(control_mean, axis=0)
    adjusted_df = adjusted_df.clip(lower=0)  # Ensure no negative values
    return adjusted_df


def method_2_blank_subtraction(control_df, experimental_df, std_deviation_factor=1):
    """
    Subtraction of the control mean and adjustment with standard deviation.
    """
    # Calculate row-wise mean and standard deviation for control samples
    control_mean = control_df.iloc[:, 5:].mean(axis=1)
    control_std = control_df.iloc[:, 5:].std(axis=1)

    # Convert mean and std to numpy arrays for proper broadcasting
    control_mean_array = control_mean.to_numpy()
    control_std_array = control_std.to_numpy()

    # Subtract control mean and apply standard deviation adjustment
    adjusted_df = experimental_df.iloc[:, 5:].sub(control_mean_array, axis=0)
    adjusted_df -= std_deviation_factor * control_std_array[:, np.newaxis]
    adjusted_df = adjusted_df.clip(lower=0)  # Ensure no negative values

    return adjusted_df, control_mean, control_std


def method_3_blank_subtraction(control_df, experimental_df):
    """
    Advanced custom subtraction logic. Modify as per requirements.
    """
    # Example: Subtract the median of the control values
    control_median = control_df.iloc[:, 5:].median(axis=1)
    adjusted_df = experimental_df.iloc[:, 5:].sub(control_median, axis=0)
    adjusted_df = adjusted_df.clip(lower=0)  # Ensure no negative values
    return adjusted_df
