import os

import numpy as np
import pandas as pd


def column_letter_to_index(letter):
    """Converts an Excel-style column letter to a zero-based integer index."""
    letter = letter.upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def read_and_filter_csv(file_path):
    """
    Reads a CSV file, selects the first 5 columns and any column containing '.d'.
    """
    print(f"Reading file: {file_path}...")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        df = pd.read_csv(file_path, low_memory=False)
        selected_columns = list(df.columns[:5]) + [
            col for col in df.columns if ".d" in col
        ]
        return df[selected_columns]
    except Exception as e:
        raise RuntimeError(f"Error processing {file_path}: {e}")


def rename_metadata_columns(df, user_mapping):
    """
    Renames DataFrame columns based on a user-provided mapping.

    Args:
        df (pd.DataFrame): The DataFrame to modify.
        user_mapping (dict): A dictionary mapping standard names to column letters.
                             Example: {'ID': 'A', 'RT': 'B', 'm/z': 'E'}

    Returns:
        pd.DataFrame: The DataFrame with renamed columns.
    """
    all_columns = df.columns.tolist()
    rename_dict = {}

    print("--- Renaming Metadata Columns ---")

    # Build the dictionary for pandas .rename() method, e.g., {'Old Name': 'New Name'}
    for standard_name, column_letter in user_mapping.items():
        try:
            index = column_letter_to_index(column_letter)
            if index >= len(all_columns):
                raise IndexError(
                    f"Column '{column_letter}' is out of bounds for this file."
                )

            old_name = all_columns[index]
            rename_dict[old_name] = standard_name

        except Exception as e:
            raise ValueError(f"Could not process mapping for '{standard_name}': {e}")

    # Apply the renaming
    df_renamed = df.rename(columns=rename_dict)

    print(f"✔️ Columns successfully renamed: {rename_dict}\n")
    return df_renamed


def separate_control_experimental(combined_data, control_samples, experimental_samples):
    """
    Separates the combined DataFrame into control and experimental DataFrames
    based on provided column name lists.
    """
    metadata_cols = combined_data.columns[:5].tolist()

    # Ensure all specified columns actually exist in the DataFrame
    for col in control_samples + experimental_samples:
        if col not in combined_data.columns:
            raise ValueError(f"Column '{col}' not found in the data.")

    control_df = combined_data[metadata_cols + control_samples]
    experimental_df = combined_data[metadata_cols + experimental_samples]

    return control_df, experimental_df


# --- NEW MODULAR FUNCTIONS FOR GUI-FRIENDLY WORKFLOW ---


def process_and_combine_files(file_paths):
    """Reads and concatenates all specified CSV files into a single DataFrame."""
    if not file_paths:
        raise ValueError("No file paths provided.")
    all_data_frames = [read_and_filter_csv(fp) for fp in file_paths]
    return pd.concat(all_data_frames, ignore_index=True)


def define_and_separate_samples(
    combined_data, control_start_col, control_end_col, exp_start_col, exp_end_col
):
    """
    Uses column boundaries to define and separate samples into control and experimental.
    """
    all_columns = combined_data.columns.tolist()
    metadata_cols = combined_data.columns[:5].tolist()

    try:
        # Define control samples from column letters
        control_start_index = column_letter_to_index(control_start_col)
        control_end_index = column_letter_to_index(control_end_col)
        control_samples = all_columns[control_start_index : control_end_index + 1]

        # Define experimental samples from column letters
        exp_start_index = column_letter_to_index(exp_start_col)
        exp_end_index = column_letter_to_index(exp_end_col)
        experimental_samples = all_columns[exp_start_index : exp_end_index + 1]

        print("--- Column Definition ---")
        print(
            f"✔️ Control columns ('{control_start_col}' to '{control_end_col}') selected: {control_samples}"
        )
        print(
            f"✔️ Experimental columns ('{exp_start_col}' to '{exp_end_col}') selected: {experimental_samples}\n"
        )

        # Create the separate dataframes
        control_df = combined_data[metadata_cols + control_samples]
        experimental_df = combined_data[metadata_cols + experimental_samples]

        # [FIX] Return all three DataFrames as expected by the main function call
        return combined_data, control_df, experimental_df

    except IndexError:
        raise ValueError(
            "A specified column letter is out of bounds for the data file."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to separate samples: {e}")


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
    group_average = round(non_zero_counts.mean())
    group_std_dev = round(non_zero_counts.std())

    return group_average, group_std_dev


def align_control_experimental(control_df, experimental_df):
    """
    Aligns the control and experimental DataFrames so that only rows present in both are retained.
    Any rows in the control set without matching rows in the experimental set are excluded.

    Args:
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.

    Returns:
        aligned_control_df (pd.DataFrame): Aligned control DataFrame.
        aligned_experimental_df (pd.DataFrame): Aligned experimental DataFrame.
    """
    # Ensure both DataFrames have the same indices
    common_indices = control_df.index.intersection(experimental_df.index)
    aligned_control_df = control_df.loc[common_indices].reset_index(drop=True)
    aligned_experimental_df = experimental_df.loc[common_indices].reset_index(drop=True)

    print(f"[DEBUG] Aligned control DataFrame shape: {aligned_control_df.shape}")
    print(
        f"[DEBUG] Aligned experimental DataFrame shape: {aligned_experimental_df.shape}"
    )

    return aligned_control_df, aligned_experimental_df


def method_1_blank_subtraction(control_df, experimental_df):
    """
    Subtracts the highest value within the control set for each row from the experimental sample set.
    Returns adjusted experimental DataFrame with the first five columns retained as identifiers.
    """
    # Calculate statistics for control and experimental sets before subtraction
    group_avg, group_std = count_non_zero_rows(control_df)
    print(
        f"Control Sample Set - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"Experimental Sample Set - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    # Calculate the maximum value in the control set for each row
    control_max = control_df.iloc[:, 5:].max(
        axis=1
    )  # Exclude the first 5 columns (metadata)

    # Subtract the maximum control value from each row in the experimental set
    adjusted_values = experimental_df.iloc[:, 5:].sub(control_max, axis=0)
    adjusted_values = adjusted_values.clip(lower=0)  # Ensure no negative values

    # Concatenate the first 5 columns as identifiers
    adjusted_df = pd.concat([experimental_df.iloc[:, :5], adjusted_values], axis=1)

    # Calculate statistics after subtraction
    group_avg, group_std = count_non_zero_rows(adjusted_values)
    print(
        f"After Blank Subtraction - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    # Calculate the control mean and control standard deviation
    control_mean = control_df.iloc[:, 5:].mean(axis=1)
    control_std = control_df.iloc[:, 5:].std(axis=1)

    return adjusted_df, control_mean, control_std


def method_2_blank_subtraction(control_df, experimental_df, std_deviation_factor=1):
    """
    Subtraction of the control mean and adjustment with standard deviation,
    while retaining identifier columns and consistent column names.

    Args:
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.
        std_deviation_factor (float): Factor for standard deviation adjustment.

    Returns:
        tuple: Adjusted experimental DataFrame with identifier columns, control mean, and control std.
    """
    # Align control and experimental DataFrames
    control_df, experimental_df = align_control_experimental(
        control_df, experimental_df
    )

    # Count rows before subtraction
    group_avg, group_std = count_non_zero_rows(control_df)
    print(
        f"Control Sample Set - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"Experimental Sample Set - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    # Calculate row-wise mean and standard deviation for control samples
    control_mean = control_df.iloc[:, 5:].mean(axis=1)
    control_std = control_df.iloc[:, 5:].std(axis=1)

    # Convert mean and std to numpy arrays for proper broadcasting
    control_mean_array = control_mean.to_numpy()
    control_std_array = control_std.to_numpy()

    # Subtract control mean and apply standard deviation adjustment
    experimental_values = experimental_df.iloc[:, 5:]
    adjusted_values = experimental_values.sub(control_mean_array, axis=0)
    adjusted_values -= std_deviation_factor * control_std_array[:, np.newaxis]
    adjusted_values = adjusted_values.clip(lower=0)  # Ensure no negative values

    # Concatenate identifier columns back with adjusted values
    adjusted_df = pd.concat([experimental_df.iloc[:, :5], adjusted_values], axis=1)

    # Ensure column consistency with method 1 (retain `m/z` naming)
    adjusted_df.rename(
        columns={
            "m/z": "m/z",
        },
        inplace=True,
    )

    # Count rows after subtraction
    group_avg, group_std = count_non_zero_rows(adjusted_values)
    print(
        f"After Blank Subtraction - Number of Features Present: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    return adjusted_df, control_mean, control_std


# Replace the existing function in your modules/blank_subtraction.py file


def perform_blank_subtraction(method, control_df, experimental_df, std_devs=3.0):
    """
    Performs blank subtraction based on the selected method.

    Args:
        method (str): The method number ('1' or '2').
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.
        std_devs (float): The number of standard deviations for Method 2, passed from the GUI.

    Returns:
        tuple: Adjusted experimental DataFrame, control mean, and control std.
    """
    if method == "1":
        # No changes needed for Method 1
        adjusted_df, control_mean, control_std = method_1_blank_subtraction(
            control_df, experimental_df
        )
        return adjusted_df, control_mean, control_std

    elif method == "2":
        # This now uses the 'std_devs' argument instead of the input() prompt
        adjusted_df, control_mean, control_std = method_2_blank_subtraction(
            control_df, experimental_df, std_deviation_factor=std_devs
        )
        return adjusted_df, control_mean, control_std

    else:
        raise ValueError("Invalid method selected. Please choose '1' or '2'.")
