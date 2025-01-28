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
    ccs_error_percentage=2,
    z=1,
):
    """
    Processes the experimental dataset to separate matched features (for the Standards Report)
    and unmatched features (for further blank subtraction workflow).
    Removes matched features from the experimental dataset.
    Adds row-level CCS percentage error, mass error, and intensity values in the Standards Report.

    Args:
        control_df (pd.DataFrame): Control sample DataFrame.
        experimental_df (pd.DataFrame): Experimental sample DataFrame.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error percentage (e.g., 2 for 2%).
        z (int): Charge state.

    Returns:
        pd.DataFrame: Experimental DataFrame with unmatched features retained.
    """
    try:
        print("[DEBUG] Loading standards library...")
        standards_df = pd.read_csv(standards_file)
        if (
            "m/z" not in standards_df.columns
            or "CCS" not in standards_df.columns
            or "Name" not in standards_df.columns
        ):
            raise ValueError(
                "Standards library must contain 'm/z', 'CCS', and 'Name' columns for matching."
            )

        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()
        standards_names = standards_df["Name"].dropna().to_numpy()

        error_standards_mz = standards_mz - 1.003355
        all_standards_mz = np.concatenate([standards_mz, error_standards_mz])
        all_standards_ccs = np.concatenate([standards_ccs, standards_ccs])
        all_standards_names = np.concatenate([standards_names, standards_names])

        experimental_mz = experimental_df.iloc[:, 4].to_numpy()
        experimental_ccs = experimental_df.iloc[:, 3].to_numpy()

        matched_indices = []
        matched_rows = []
        error_matched_rows = []
        d_columns = [col for col in experimental_df.columns if ".d" in col]

        for i, (mz, ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs, std_name in zip(
                all_standards_mz, all_standards_ccs, all_standards_names
            ):
                try:
                    mass_bound = mz * mass_error_ppm * 1e-6 / z
                    lower_bound = std_mz - mass_bound
                    upper_bound = std_mz + mass_bound
                    ccs_error = round(abs(ccs - std_ccs) / std_ccs * 100, 2)

                    matches_standard = (
                        lower_bound <= mz <= upper_bound
                        and ccs_error <= ccs_error_percentage
                    )

                    if matches_standard:
                        row_values = experimental_df.iloc[i][d_columns]
                        non_zero_count = (row_values > 0.001).sum()
                        total_count = len(d_columns)
                        sample_coverage = round((non_zero_count / total_count) * 100, 2)

                        intensity_values = {
                            f"Intensity ({col})": experimental_df.iloc[i][col]
                            for col in d_columns
                        }
                        matched_row = experimental_df.iloc[i, :5].to_dict()
                        matched_row.update(
                            {
                                "Experimental m/z": mz,
                                "Experimental CCS": ccs,
                                "Standard m/z": std_mz,
                                "Standard CCS": std_ccs,
                                "Name": std_name,
                                "Sample Coverage (%)": sample_coverage,
                                "Mass Error (ppm)": round(
                                    (mz - std_mz) / std_mz * 1e6, 2
                                ),
                                "CCS Error (%)": ccs_error,
                            }
                        )
                        matched_row.update(intensity_values)

                        if std_mz in error_standards_mz:
                            error_matched_rows.append(matched_row)
                        else:
                            matched_rows.append(matched_row)

                        matched_indices.append(i)
                        break
                except Exception as e:
                    print(f"[ERROR] Matching failed for row {i}: {e}")

        unmatched_experimental_df = experimental_df.drop(index=matched_indices)

        output_folder = "PIMMS v1.2/.temp"
        os.makedirs(output_folder, exist_ok=True)

        edit_and_save_standards_report(
            matched_rows=matched_rows,
            standards_file=standards_file,  # Pass the standards_file here
            output_folder="PIMMS v1.2/.temp",
            file_name="Standards_report.csv",
        )
        edit_and_save_standards_report(
            matched_rows=error_matched_rows,
            standards_file=standards_file,  # Pass the standards_file here
            output_folder="PIMMS v1.2/.temp",
            file_name="Standards_error_report.csv",
        )
        print(f"[DEBUG] Total matched rows: {len(matched_rows)}")
        print(f"[DEBUG] Total error matched rows: {len(error_matched_rows)}")
        print(
            f"[DEBUG] Total unmatched rows: {len(experimental_df) - len(matched_indices)}"
        )

        return unmatched_experimental_df

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        return experimental_df


def process_standards_report_only(
    experimental_df,
    standards_file,
    mass_error_ppm=10,
    ccs_error_percentage=2,
    z=1,
):
    """
    Creates a Standards Report by matching features in the experimental dataset
    to the standards library without removing the matched peaks from the dataset.

    Args:
        experimental_df (pd.DataFrame): Experimental sample DataFrame.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error percentage (e.g., 2 for 2%).
        z (int): Charge state.

    Returns:
        None: Generates and saves a Standards Report CSV file.
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

        # Add error standards to standards_mz
        error_standards_mz = standards_mz - 1.003355
        standards_mz = np.concatenate([standards_mz, error_standards_mz])
        standards_ccs = np.concatenate([standards_ccs, standards_ccs])  # Duplicate CCS

        print(
            f"[DEBUG] Standards library loaded with {len(standards_mz)} 'm/z' values "
            f"and {len(standards_ccs)} 'CCS' values."
        )

        # Compare "m/z" and "CCS" in the experimental dataset
        experimental_mz = experimental_df.iloc[:, 4].to_numpy()
        experimental_ccs = experimental_df.iloc[:, 3].to_numpy()

        print(
            f"[DEBUG] Experimental dataset contains {len(experimental_mz)} 'm/z' values "
            f"and {len(experimental_ccs)} 'CCS' values."
        )

        matched_rows = []  # Store matched experimental and standards rows

        # Identify `.d` columns for intensity calculations
        d_columns = [col for col in experimental_df.columns if ".d" in col]

        print("[DEBUG] Iterating through experimental dataset...")
        for i, (mz, ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                try:
                    # Calculate mass and CCS bounds
                    mass_bound = mz * mass_error_ppm * 1e-6 / z
                    lower_bound = std_mz - mass_bound
                    upper_bound = std_mz + mass_bound
                    ccs_error = round(abs(ccs - std_ccs) / std_ccs * 100, 2)

                    # Check if experimental value matches the standard
                    matches_standard = (
                        lower_bound <= mz <= upper_bound
                        and ccs_error <= ccs_error_percentage
                    )

                    if matches_standard:
                        row_values = experimental_df.iloc[i][d_columns]
                        non_zero_count = (row_values > 0.001).sum()
                        total_count = len(d_columns)
                        sample_coverage = round((non_zero_count / total_count) * 100, 2)

                        intensity_values = {
                            f"Intensity ({col})": experimental_df.iloc[i][col]
                            for col in d_columns
                        }
                        matched_row = experimental_df.iloc[i, :5].to_dict()
                        matched_row.update(
                            {
                                "Experimental m/z": mz,
                                "Experimental CCS": ccs,
                                "Standard m/z": std_mz,
                                "Standard CCS": std_ccs,
                                "Sample Coverage (%)": sample_coverage,
                                "Mass Error (ppm)": round(
                                    (mz - std_mz) / std_mz * 1e6, 2
                                ),
                                "CCS Error (%)": ccs_error,
                            }
                        )
                        matched_row.update(intensity_values)

                        matched_rows.append(matched_row)
                        break  # Stop further checks after finding a match
                except Exception as e:
                    print(f"[ERROR] Exception while checking match for Row {i}: {e}")

        # Use the new function to handle editing and saving the standards report
        edit_and_save_standards_report(matched_rows)

        print(f"[DEBUG] Total matched rows: {len(matched_rows)}")

    except FileNotFoundError:
        print("Error: Standards library file not found.")
    except Exception as e:
        print(f"[ERROR] Error during standards report generation: {e}")


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
    print(f"[DEBUG] Initial matched rows DataFrame:\n{matched_df.head()}")

    # Ensure necessary columns are present
    required_columns = {"Experimental m/z", "Experimental CCS", "RT"}
    if not required_columns.issubset(matched_df.columns):
        raise ValueError(f"Matched rows must include {required_columns} columns.")
    print("[DEBUG] All required columns are present.")

    # Sort for grouping
    matched_df = matched_df.sort_values(
        by=["Experimental m/z", "Experimental CCS", "RT"]
    )
    print(f"[DEBUG] Sorted matched DataFrame:\n{matched_df.head()}")

    # Initialize list for consolidated rows
    consolidated_rows = []

    # Iterate to combine rows
    iteration_count = 0
    while not matched_df.empty:
        iteration_count += 1
        print(f"[DEBUG] Iteration {iteration_count}, remaining rows: {len(matched_df)}")

        # Take the first row as the base
        base_row = matched_df.iloc[0]
        mz_base = base_row["Experimental m/z"]
        ccs_base = base_row["Experimental CCS"]
        rt_base = base_row["RT"]
        print(
            f"[DEBUG] Base row selected:\nm/z={mz_base}, CCS={ccs_base}, RT={rt_base}"
        )

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
        print(f"[DEBUG] Rows in group (iteration {iteration_count}):\n{in_group}")

        # Remove grouped rows from the DataFrame
        matched_df = matched_df.drop(in_group.index)
        print(
            f"[DEBUG] Remaining rows after drop (iteration {iteration_count}):\n{matched_df}"
        )

        # Consolidate data
        combined_row = base_row.to_dict()
        for col in [c for c in in_group.columns if ".d" in c]:
            # Combine intensities for each `.d` column separately
            combined_row[col] = in_group[col].max()
            print(f"[DEBUG] Combined intensity for {col}: {combined_row[col]}")

        # Calculate sample coverage
        non_zero_count = sum(
            1 for col in in_group.columns if ".d" in col and combined_row[col] > 0.001
        )
        total_count = sum(1 for col in in_group.columns if ".d" in col)
        combined_row["Sample Coverage (%)"] = (
            (non_zero_count / total_count) * 100 if total_count > 0 else 0
        )
        print(
            f"[DEBUG] Sample Coverage (%) for combined row: {combined_row['Sample Coverage (%)']}"
        )

        consolidated_rows.append(combined_row)
        print(f"[DEBUG] Combined row (iteration {iteration_count}):\n{combined_row}")

    print(f"[DEBUG] Final consolidated rows: {len(consolidated_rows)}")
    return consolidated_rows


def edit_and_save_standards_report(
    matched_rows, standards_file, output_folder, file_name="Standards_report.csv"
):
    """
    Edits and saves the matched standards report, ensuring unmatched standards are included.

    Args:
        matched_rows (list): List of dictionaries containing matched rows data.
        standards_file (str): Path to the standards library CSV file.
        output_folder (str): Folder path to save the standards report.
        file_name (str): Name of the output file.
    """
    if not matched_rows:
        print("No matches found. Standards report is empty.")
        return

    try:
        print("[DEBUG] Loading standards library for unmatched standards...")
        standards_df = pd.read_csv(standards_file)
        if (
            "m/z" not in standards_df.columns
            or "CCS" not in standards_df.columns
            or "Name" not in standards_df.columns
        ):
            raise ValueError(
                "Standards library must contain 'm/z', 'CCS', and 'Name' columns."
            )

        # Create a DataFrame for matched rows
        print("[DEBUG] Combining matched rows...")
        consolidated_rows = combine_matched_rows(
            matched_rows, mass_error_ppm=10, ccs_error_percentage=2, rt_tolerance=0.5
        )
        print(f"[DEBUG] combine_matched_rows returned {len(consolidated_rows)} rows.")
        matched_standards_df = pd.DataFrame(consolidated_rows)

        # Ensure all standards are included
        unmatched_rows = []
        for _, standard in standards_df.iterrows():
            std_name = standard["Name"]
            if std_name not in matched_standards_df["Name"].values:
                unmatched_row = {
                    "Standard m/z": standard["m/z"],
                    "Standard CCS": standard["CCS"],
                    "Name": std_name,
                    "Experimental m/z": "NA",
                    "Experimental CCS": "NA",
                    "Experimental DT": "NA",  # Adding "Experimental DT" for unmatched standards
                    "Sample Coverage (%)": 0,
                    "Mass Error (ppm)": "NA",
                    "CCS Error (%)": "NA",
                }
                unmatched_rows.append(unmatched_row)

        unmatched_df = pd.DataFrame(unmatched_rows)

        # Combine matched and unmatched rows
        final_report_df = pd.concat(
            [matched_standards_df, unmatched_df], ignore_index=True
        )

        # Drop unnecessary columns and rename `DT` to `Experimental DT`
        final_report_df = final_report_df.drop(columns=["CCS", "m/z"], errors="ignore")
        if "DT" in final_report_df.columns:
            final_report_df.rename(columns={"DT": "Experimental DT"}, inplace=True)

        # Save the edited report
        os.makedirs(output_folder, exist_ok=True)
        report_file = os.path.join(output_folder, file_name)
        final_report_df.to_csv(report_file, index=False)
        print(f"[DEBUG] Standards report saved to {report_file}")

        # Summary
        print(
            f"Standards report saved to {report_file}\n"
            f"Total Matches: {len(matched_standards_df)}\n"
            f"Unmatched Standards: {len(unmatched_rows)}\n"
            f"Total Standards: {len(final_report_df)}"
        )

    except Exception as e:
        print(f"[ERROR] Failed to edit and save standards report: {e}")
