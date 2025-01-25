import os

import numpy as np
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

        # Select the first 5 columns and any column containing '.d'
        selected_columns = list(df.columns[:5]) + [
            col for col in df.columns if ".d" in col
        ]
        filtered_df = df[selected_columns]

        return filtered_df
    except Exception as e:
        raise RuntimeError(f"Error processing {file_path}: {e}")


def separate_control_experimental(combined_data, control_samples):
    """
    Separates the combined DataFrame into control and experimental DataFrames.

    Args:
        combined_data (pd.DataFrame): The combined data containing all samples.
        control_samples (list): List of control sample column names.

    Returns:
        control_df (pd.DataFrame): DataFrame containing control samples and metadata.
        experimental_df (pd.DataFrame): DataFrame containing experimental samples.
    """
    # Ensure all control columns are present
    for col in control_samples:
        if col not in combined_data.columns:
            raise ValueError(f"Control column '{col}' not found in the data.")

    # Select control samples and metadata (first 5 columns)
    control_df = combined_data[combined_data.columns[:5].tolist() + control_samples]

    # Select experimental samples (all other '.d' columns not in control_samples)
    experimental_columns = [
        col
        for col in combined_data.columns
        if col not in control_df.columns and ".d" in col
    ]
    experimental_df = combined_data[
        combined_data.columns[:5].tolist() + experimental_columns
    ]

    return control_df, experimental_df


def count_non_zero_rows(df):
    """
    Calculates the group average and standard deviation of rows with values greater than 0.001
    in all '.d' columns.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        tuple: Group average and group standard deviation of non-zero rows.
    """
    # Identify all '.d' columns
    d_columns = [col for col in df.columns if ".d" in col]
    if not d_columns:
        print("No '.d' columns found in the DataFrame.")
        return 0, 0

    # Calculate the proportion of non-zero values (greater than 0.001) for each row
    non_zero_counts = df[d_columns].apply(
        lambda col: pd.to_numeric(col, errors="coerce").fillna(0).gt(0.001).sum()
    )

    # Calculate group average and standard deviation
    group_average = non_zero_counts.mean()
    group_std_dev = non_zero_counts.std()

    return group_average, group_std_dev


def method_1_blank_subtraction(control_df, experimental_df):
    """
    Basic subtraction of the control mean from experimental samples.
    """
    group_avg, group_std = count_non_zero_rows(control_df)
    print(
        f"Control Sample Set - Average Non-Zero Proportion: {group_avg:.4f}, Std Dev: {group_std:.4f}"
    )
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"Experimental Sample Set - Average Non-Zero Proportion: {group_avg:.4f}, Std Dev: {group_std:.4f}"
    )
    control_mean = control_df.iloc[:, 5:].mean(axis=1)  # Exclude first 5 columns
    adjusted_df = experimental_df.iloc[:, 5:].sub(control_mean, axis=0)
    adjusted_df = adjusted_df.clip(lower=0)  # Ensure no negative values
    group_avg, group_std = count_non_zero_rows(adjusted_df)
    print(
        f"After Blank Subtraction - Average Non-Zero Proportion: {group_avg:.4f}, Std Dev: {group_std:.4f}"
    )

    return adjusted_df


def method_2_blank_subtraction(control_df, experimental_df, std_deviation_factor=1):
    """
    Subtraction of the control mean and adjustment with standard deviation,
    with non-zero row counts before and after subtraction.

    Args:
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.
        std_deviation_factor (float): Factor for standard deviation adjustment.

    Returns:
        tuple: Adjusted experimental DataFrame, control mean, and control std.
    """
    # Count rows before subtraction
    group_avg, group_std = count_non_zero_rows(control_df)
    print(
        f"Control Sample Set  - Average Non-Zero Rows: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"Experimental Sample Set - Average Non-Zero Rows: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

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

    # Count rows after subtraction
    group_avg, group_std = count_non_zero_rows(adjusted_df)
    print(
        f"Experimental Sample Set After Blank Subtraction - Average Non-Zero Rows: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )
    return adjusted_df, control_mean, control_std
