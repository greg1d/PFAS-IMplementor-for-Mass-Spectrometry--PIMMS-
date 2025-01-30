import os
import sys

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (
    method_1_blank_subtraction,
    method_2_blank_subtraction,
    read_and_filter_csv,
    separate_control_experimental,
)


def process_files(file_paths, control_samples):
    """
    Reads and combines data from multiple files, separating control and experimental samples.

    Args:
        file_paths (list): List of file paths to read.
        control_samples (list): Columns to consider as control samples.

    Returns:
        tuple: Combined DataFrame, control DataFrame, experimental DataFrame.
    """
    combined_data = pd.DataFrame()

    print("Reading and filtering data from multiple files...")
    for file_path in file_paths:
        try:
            filtered_data = read_and_filter_csv(file_path)
            combined_data = pd.concat([combined_data, filtered_data], ignore_index=True)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    if combined_data.empty:
        raise ValueError("No valid data loaded from the files.")

    # Separate control and experimental data
    control_df, experimental_df = separate_control_experimental(
        combined_data, control_samples
    )

    return combined_data, control_df, experimental_df


def perform_blank_subtraction(method, control_df, experimental_df):
    """
    Performs blank subtraction based on the selected method.

    Args:
        method (str): The method number ('1', '2', or '3').
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.

    Returns:
        pd.DataFrame: Adjusted experimental DataFrame.
    """
    if method == "1":
        adjusted_df, control_mean, control_std = method_1_blank_subtraction(
            control_df, experimental_df
        )

        return adjusted_df, control_mean, control_std

    elif method == "2":
        std_deviation_factor = float(
            input("Enter the number of standard deviations for subtraction: ")
        )
        adjusted_df, control_mean, control_std = method_2_blank_subtraction(
            control_df, experimental_df, std_deviation_factor
        )
        return adjusted_df, control_mean, control_std

    else:
        raise ValueError("Invalid method selected.")
