import bisect
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
    Subtracts the highest value within the control set for each row from the experimental sample set.
    Returns adjusted experimental DataFrame and statistics (control mean and control std).
    """
    # Calculate statistics for control and experimental sets before subtraction
    group_avg, group_std = count_non_zero_rows(control_df)
    print(
        f"Control Sample Set - Average Non-Zero Proportion: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"Experimental Sample Set - Average Non-Zero Proportion: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    # Calculate the maximum value in the control set for each row
    control_max = control_df.iloc[:, 5:].max(
        axis=1
    )  # Exclude the first 5 columns (metadata)

    # Subtract the maximum control value from each row in the experimental set
    adjusted_df = experimental_df.iloc[:, 5:].sub(control_max, axis=0)
    adjusted_df = adjusted_df.clip(lower=0)  # Ensure no negative values

    # Calculate statistics after subtraction
    group_avg, group_std = count_non_zero_rows(adjusted_df)
    print(
        f"After Blank Subtraction - Average Non-Zero Proportion: {group_avg:.0f}, Std Dev: {group_std:.0f}"
    )

    # Calculate the control mean and control standard deviation
    control_mean = control_df.iloc[:, 5:].mean(axis=1)
    control_std = control_df.iloc[:, 5:].std(axis=1)

    return adjusted_df, control_mean, control_std


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


def save_adjusted_dataset(adjusted_df, original_df):
    """
    Saves the adjusted dataset into a .temp folder with a filename that includes the current date and time.
    Removes rows with empty cells before saving.

    Args:
        adjusted_df (pd.DataFrame): The adjusted experimental dataset.
        original_df (pd.DataFrame): The original dataset for metadata (first 5 columns).
    """
    # Create .temp folder if it doesn't exist
    temp_folder = "PIMMS v1.2/.temp"
    os.makedirs(temp_folder, exist_ok=True)

    # Combine metadata (first 5 columns) with the adjusted dataset
    combined_df = pd.concat([original_df.iloc[:, :5], adjusted_df], axis=1)

    # Drop rows with any missing values
    combined_df = combined_df.dropna(how="any")

    # Generate a filename with the current date and time
    file_name = "blank_subtracted_dataset.csv"
    file_path = os.path.join(temp_folder, file_name)

    # Save the cleaned dataset as a CSV file
    combined_df.to_csv(file_path, index=False)
    print(f"Blank-subtracted dataset saved to {file_path}")


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
    control_df,
    experimental_df,
    standards_file,
    mass_error_ppm=10,
    ccs_error_percentage=0.02,
    z=1,
):
    """
    Processes the experimental dataset to separate matched features (for the Standards Report)
    and unmatched features (for further blank subtraction workflow).
    Exports a report of all matched entries including experimental values, matched reference values,
    and additional metadata. Filters out rows with empty cells in `.d` columns before saving.

    Args:
        control_df (pd.DataFrame): Control sample DataFrame.
        experimental_df (pd.DataFrame): Experimental sample DataFrame.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        z (int): Charge state.

    Returns:
        pd.DataFrame: Experimental DataFrame with unmatched features retained.
    """
    try:
        print("[DEBUG] Loading standards library...")
        # Load the standards library
        standards_df = pd.read_csv(standards_file)
        if "m/z" not in standards_df.columns or "CCS" not in standards_df.columns:
            raise ValueError(
                "Standards library must contain 'm/z' and 'CCS' columns for matching."
            )

        # Extract "m/z" and "CCS" values from the standards library
        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()

        print(
            f"[DEBUG] Standards library loaded with {len(standards_mz)} 'm/z' and {len(standards_ccs)} 'CCS' values."
        )

        # Compare "m/z" (5th column) and "CCS" (4th column) in the experimental dataset
        experimental_mz = experimental_df.iloc[:, 4].to_numpy()  # Column E (5th column)
        experimental_ccs = experimental_df.iloc[
            :, 3
        ].to_numpy()  # Column D (4th column)

        print(
            f"[DEBUG] Experimental dataset contains {len(experimental_mz)} 'm/z' and {len(experimental_ccs)} 'CCS' values."
        )

        matched_rows = []  # To store the report data for matched experimental and standards values
        unmatched_indices = []  # Indices of experimental rows not matched

        # Identify `.d` columns for empty cell filtering later
        d_columns = [col for col in experimental_df.columns if ".d" in col]

        # Debug the standard and experimental values
        print("[DEBUG] Iterating through experimental dataset...")
        for i, (mz, ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            is_matched = False  # Flag to track if a match is found
            for j, (std_mz, std_ccs) in enumerate(zip(standards_mz, standards_ccs)):
                try:
                    # Calculate mass error bounds for the current standard m/z
                    mass_bound = calculate_mass_error(std_mz, mass_error_ppm, z)
                    lower_bound = std_mz - mass_bound
                    upper_bound = std_mz + mass_bound

                    # Check if the experimental m/z falls within the bounds
                    matches_standard = (
                        lower_bound <= mz <= upper_bound
                        and abs(ccs - std_ccs) / std_ccs <= ccs_error_percentage
                    )

                    if matches_standard:
                        print(
                            f"[DEBUG] Match found for experimental row {i}: "
                            f"Experimental m/z={mz:.4f}, CCS={ccs:.4f}; "
                            f"Standard m/z={std_mz:.4f}, CCS={std_ccs:.4f}"
                        )

                        # Add match to the Standards Report
                        matched_row = experimental_df.iloc[i, :5].to_dict()
                        matched_row.update(
                            {
                                "Experimental m/z": mz,
                                "Experimental CCS": ccs,
                                "Standard m/z": std_mz,
                                "Standard CCS": std_ccs,
                            }
                        )
                        matched_rows.append(matched_row)
                        is_matched = True
                        break  # No need to check further standards for this experimental row

                except Exception as e:
                    print(
                        f"[ERROR] Exception while checking match for experimental row {i} and standard {j}: {e}"
                    )

            if not is_matched:
                unmatched_indices.append(i)

        print(f"[DEBUG] Total matched rows: {len(matched_rows)}")
        print(f"[DEBUG] Total unmatched rows: {len(unmatched_indices)}")

        # Create DataFrame for unmatched features
        unmatched_experimental_df = experimental_df.iloc[unmatched_indices]

        # Remove rows with empty cells in `.d` columns from the unmatched experimental DataFrame
        unmatched_experimental_df = unmatched_experimental_df.dropna(
            subset=d_columns, how="any"
        )
        print(
            f"[DEBUG] Unmatched experimental features after filtering empty `.d` cells: {len(unmatched_experimental_df)}"
        )

        # Save the matched standards report
        temp_folder = "PIMMS v1.2/.temp"
        os.makedirs(temp_folder, exist_ok=True)

        standards_report_file = os.path.join(temp_folder, "Standards_report.csv")
        matched_standards_df = pd.DataFrame(matched_rows)
        matched_standards_df.to_csv(standards_report_file, index=False)
        print(f"Standards report saved to {standards_report_file}")

        return unmatched_experimental_df

    except FileNotFoundError:
        print("Error: Standards library file not found.")
        return experimental_df
    except Exception as e:
        print(f"Error during standards library removal: {e}")
        return experimental_df
