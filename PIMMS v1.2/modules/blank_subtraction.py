import bisect
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


def calculate_mass_error(mass, mass_error_ppm=10, z=1):
    """
    Calculate the mass error bounds based on mass, ppm, and charge state.
    """
    mass_error = mass * mass_error_ppm * 1e-6
    mass_bound = mass_error / z
    return mass_bound


def find_peaks_within_bounds(array, z, M, i, mass_error_ppm=10):
    """
    Finds peaks within the mass error bounds of a specific peak.

    Args:
        array (list): Array of masses to search within.
        z (int): Charge state.
        M (float): Experimental mass to compare.
        i (int): Current index in the array.
        mass_error_ppm (float): Mass error tolerance in ppm.

    Returns:
        tuple: List of peaks within bounds and the count of matches.
    """
    mass_bound = calculate_mass_error(array[i], mass_error_ppm, z)
    lower_bound = array[i] + (M / z) - mass_bound
    upper_bound = array[i] + (M / z) + mass_bound

    # Find the bounds using binary search
    j_start = bisect.bisect_left(array, lower_bound, i + 1)
    j_end = bisect.bisect_right(array, upper_bound, i + 1)

    # Collect all peaks within the bounds
    peaks_within_bounds = []
    for j in range(j_start, j_end):
        peaks_within_bounds.append(array[j])
    return peaks_within_bounds, j_end - j_start


def remove_standards_library(
    adjusted_df,
    standards_file,
    mass_error_ppm,
    ccs_error_percentage,
    z,
):
    """
    Removes features from the adjusted dataset that match the m/z and CCS
    values found in a standards library.

    Args:
        adjusted_df (pd.DataFrame): The DataFrame to be filtered.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error tolerance as a percentage.
        z (int): Charge state.

    Returns:
        pd.DataFrame: The DataFrame with matched features removed.
    """
    try:
        # --- 1. Load Standards Library (Name column is no longer required) ---
        print("[INFO] Loading standards library to identify features for removal...")
        standards_df = pd.read_csv(standards_file)

        required_columns = {"m/z", "CCS"}
        if not required_columns.issubset(standards_df.columns):
            raise ValueError(
                f"Standards library must contain {required_columns} columns."
            )

        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()

        # --- 2. Prepare Experimental Data ---
        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Input DataFrame must contain 'm/z' and 'CCS' columns.")

        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()

        # --- 3. Find Indices of Matched Features ---
        # We will directly collect the indices of rows to be dropped.
        matched_indices = set()
        for i, (exp_mz, exp_ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                mass_tolerance = exp_mz * mass_error_ppm * 1e-6 / z
                ccs_tolerance = std_ccs * ccs_error_percentage / 100

                # Check if the experimental feature falls within the standard's tolerance
                if (
                    std_mz - mass_tolerance <= exp_mz <= std_mz + mass_tolerance
                    and std_ccs - ccs_tolerance <= exp_ccs <= std_ccs + ccs_tolerance
                ):
                    # If a match is found, add its index to the set and stop checking this feature
                    matched_indices.add(adjusted_df.index[i])
                    break

        # --- 4. Remove Matched Rows ---
        # The consolidation step is no longer needed.
        unmatched_df = adjusted_df.drop(index=list(matched_indices), errors="ignore")

        print(
            f"[INFO] Found and removed {len(matched_indices)} features matching the standards library."
        )
        print(f"[INFO] Remaining features: {len(unmatched_df)}")

        return unmatched_df

    except Exception as e:
        print(f"[ERROR] Failed to remove standards: {e}")
        return adjusted_df


def combine_matched_rows(
    matched_rows, mass_error_ppm, ccs_error_percentage, rt_tolerance
):
    """
    Combines matched rows within specified tolerances for m/z, CCS, and RT.

    Args:
        matched_rows (list of dict): List of matched rows to process.
        mass_error_ppm (float): Tolerance for m/z in parts per million (ppm).
        ccs_error_percentage (float): Tolerance for CCS as a percentage.
        rt_tolerance (float): Tolerance for RT in minutes.

    Returns:
        list of dict: Consolidated matched rows.
    """
    print("[DEBUG] combine_matched_rows function has been called.")

    # Convert matched rows to a DataFrame
    matched_df = pd.DataFrame(matched_rows)

    # Ensure necessary columns are present
    required_columns = {"Experimental m/z", "Experimental CCS", "RT"}
    if not required_columns.issubset(matched_df.columns):
        raise ValueError(f"Matched rows must include {required_columns} columns.")
    print("[DEBUG] All required columns are present.")

    # Sort for grouping
    matched_df = matched_df.sort_values(
        by=["Experimental m/z", "Experimental CCS", "RT"]
    )

    # Initialize list for consolidated rows
    consolidated_rows = []

    # Iterate to combine rows
    iteration_count = 0
    while not matched_df.empty:
        iteration_count += 1

        # Take the first row as the base
        base_row = matched_df.iloc[0]
        mz_base = base_row["Experimental m/z"]
        ccs_base = base_row["Experimental CCS"]
        rt_base = base_row["RT"]

        # Identify rows within tolerances
        in_group = matched_df[
            (
                matched_df["Experimental m/z"].sub(mz_base).div(mz_base).abs() * 1e6
                <= mass_error_ppm
            )
            & (
                matched_df["Experimental CCS"].sub(ccs_base).div(ccs_base).abs() * 100
                <= ccs_error_percentage
            )
            & (matched_df["RT"].sub(rt_base).abs() <= rt_tolerance)
        ]

        # Remove grouped rows from the DataFrame
        matched_df = matched_df.drop(in_group.index)

        # Consolidate data
        combined_row = base_row.to_dict()
        for col in [c for c in in_group.columns if ".d" in c]:
            # Combine intensities for each `.d` column separately
            combined_row[col] = in_group[col].max()

        # Calculate sample coverage
        non_zero_count = sum(
            1 for col in in_group.columns if ".d" in col and combined_row[col] > 0.001
        )
        total_count = sum(1 for col in in_group.columns if ".d" in col)
        combined_row["Sample Coverage (%)"] = (
            (non_zero_count / total_count) * 100 if total_count > 0 else 0
        )

        consolidated_rows.append(combined_row)

    print(f"[DEBUG] Final consolidated rows: {len(consolidated_rows)}")
    return consolidated_rows
