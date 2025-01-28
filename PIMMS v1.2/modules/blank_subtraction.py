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
    print(adjusted_df.head())
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
    adjusted_df,
    standards_file,
    mass_error_ppm=10,
    ccs_error_percentage=2,
    rt_tolerance=0.5,
    z=1,
):
    """
    Processes the adjusted dataset to separate matched features and unmatched features.
    Removes matched features from the adjusted dataset and consolidates similar rows.

    Args:
        adjusted_df (pd.DataFrame): Adjusted sample DataFrame after blank subtraction.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error percentage (e.g., 2 for 2%).
        rt_tolerance (float): RT tolerance in minutes.
        z (int): Charge state.

    Returns:
        pd.DataFrame: Adjusted DataFrame with unmatched features retained.
    """
    try:
        print("[DEBUG] Loading standards library...")
        standards_df = pd.read_csv(standards_file)

        # Ensure required columns exist
        required_columns = {"m/z", "CCS", "Name"}
        if not required_columns.issubset(standards_df.columns):
            raise ValueError(f"Standards library must contain {required_columns}.")

        # Extract standards data
        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()
        standards_names = standards_df["Name"].dropna().to_numpy()

        # Validate adjusted_df contains necessary columns
        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Adjusted dataset must contain 'm/z' and 'CCS' columns.")

        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()
        experimental_rt = adjusted_df["RT"].to_numpy()

        # Match standards against the adjusted dataset
        matched_rows = []
        for i, (mz, ccs, rt) in enumerate(
            zip(experimental_mz, experimental_ccs, experimental_rt)
        ):
            for std_mz, std_ccs, std_name in zip(
                standards_mz, standards_ccs, standards_names
            ):
                mass_tolerance = mz * mass_error_ppm * 1e-6 / z
                ccs_tolerance = std_ccs * ccs_error_percentage / 100

                if (
                    std_mz - mass_tolerance <= mz <= std_mz + mass_tolerance
                    and std_ccs - ccs_tolerance <= ccs <= std_ccs + ccs_tolerance
                ):
                    matched_row = adjusted_df.iloc[i].to_dict()
                    matched_row.update(
                        {
                            "Experimental m/z": mz,
                            "Experimental CCS": ccs,
                            "Standard m/z": std_mz,
                            "Standard CCS": std_ccs,
                            "Name": std_name,
                            "Mass Error (ppm)": round((mz - std_mz) / std_mz * 1e6, 2),
                            "CCS Error (%)": round(
                                abs(ccs - std_ccs) / std_ccs * 100, 2
                            ),
                        }
                    )
                    matched_rows.append(matched_row)
                    break

        # Consolidate matched rows using combine_matched_rows
        print("[DEBUG] Consolidating matched rows...")
        consolidated_rows = combine_matched_rows(
            matched_rows, mass_error_ppm, ccs_error_percentage, rt_tolerance
        )
        print(f"[DEBUG] Consolidated matched rows: {len(consolidated_rows)}")

        # Identify indices to remove
        matched_indices = [
            adjusted_df.index[adjusted_df["m/z"] == row["Experimental m/z"]][0]
            for row in consolidated_rows
        ]

        # Remove matched rows from the adjusted dataset
        unmatched_df = adjusted_df.drop(index=matched_indices, errors="ignore")
        print(f"[DEBUG] Matched rows removed: {len(matched_indices)}")
        print(f"[DEBUG] Remaining unmatched rows: {len(unmatched_df)}")

        return unmatched_df

    except Exception as e:
        print(f"[ERROR] Failed to remove standards: {e}")
        return adjusted_df


def process_standards_report_only(
    experimental_df,
    standards_file,
    mass_error_ppm=10,
    ccs_error_percentage=2,
    rt_tolerance=0.5,
    z=1,
):
    """
    Creates a Standards Report by matching features in the experimental dataset
    to the standards library and consolidating matched rows within tolerances.
    Rows with no matches are also included in the report with NA values.

    Args:
        experimental_df (pd.DataFrame): Experimental sample DataFrame.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error percentage (e.g., 2 for 2%).
        rt_tolerance (float): RT tolerance in minutes.
        z (int): Charge state.

    Returns:
        None: Generates and saves a Standards Report CSV file.
    """
    try:
        print("[DEBUG] Loading standards library...")
        # Load the standards library
        standards_df = pd.read_csv(standards_file)

        # Ensure the required columns exist in the standards file
        required_columns = {"m/z", "CCS", "Name"}
        if not required_columns.issubset(set(standards_df.columns)):
            raise ValueError(
                f"Standards library must contain {required_columns} columns."
            )

        # Extract standard values
        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()
        standards_names = standards_df["Name"].dropna().to_numpy()

        # Validate experimental_df contains necessary columns
        if not {"m/z", "CCS", "RT"}.issubset(experimental_df.columns):
            raise ValueError(
                "Experimental dataset must contain 'm/z', 'CCS', and 'RT' columns."
            )

        experimental_mz = experimental_df["m/z"].to_numpy()
        experimental_ccs = experimental_df["CCS"].to_numpy()
        experimental_rt = experimental_df["RT"].to_numpy()

        matched_rows = []
        unmatched_standards = []
        d_columns = [col for col in experimental_df.columns if ".d" in col]

        print("[DEBUG] Iterating through standards library...")
        for std_mz, std_ccs, std_name in zip(
            standards_mz, standards_ccs, standards_names
        ):
            matched = False
            for i, (mz, ccs, rt) in enumerate(
                zip(experimental_mz, experimental_ccs, experimental_rt)
            ):
                try:
                    # Calculate mass and CCS tolerances
                    mass_tolerance = mz * mass_error_ppm * 1e-6 / z
                    ccs_tolerance = std_ccs * ccs_error_percentage / 100

                    if (
                        std_mz - mass_tolerance <= mz <= std_mz + mass_tolerance
                        and std_ccs - ccs_tolerance <= ccs <= std_ccs + ccs_tolerance
                    ):
                        # Gather row information for reporting
                        row_values = experimental_df.iloc[i][d_columns]
                        non_zero_count = (row_values > 0.001).sum()
                        total_count = len(d_columns)
                        sample_coverage = round((non_zero_count / total_count) * 100, 2)

                        matched_row = {
                            "Experimental m/z": mz,
                            "Experimental CCS": ccs,
                            "RT": rt,
                            "Standard m/z": std_mz,
                            "Standard CCS": std_ccs,
                            "Name": std_name,
                            "Sample Coverage (%)": sample_coverage,
                            "Mass Error (ppm)": round((mz - std_mz) / std_mz * 1e6, 2),
                            "CCS Error (%)": round(
                                abs(ccs - std_ccs) / std_ccs * 100, 2
                            ),
                        }
                        matched_row.update(
                            {
                                f"Intensity ({col})": experimental_df.iloc[i][col]
                                for col in d_columns
                            }
                        )
                        matched_rows.append(matched_row)
                        matched = True
                        break
                except Exception as e:
                    print(f"[ERROR] Matching failed for row {i}: {e}")
            if not matched:
                # Add unmatched standard to the report
                unmatched_standards.append(
                    {
                        "Standard m/z": std_mz,
                        "Standard CCS": std_ccs,
                        "Name": std_name,
                        "Experimental m/z": "NA",
                        "Experimental CCS": "NA",
                        "RT": "NA",
                        "Sample Coverage (%)": 0,
                        "Mass Error (ppm)": "NA",
                        "CCS Error (%)": "NA",
                    }
                )

        # Combine matched and unmatched rows
        print("[DEBUG] Consolidating matched rows...")
        consolidated_rows = combine_matched_rows(
            matched_rows, mass_error_ppm, ccs_error_percentage, rt_tolerance
        )
        final_report = consolidated_rows + unmatched_standards
        print(f"[DEBUG] Total rows in report: {len(final_report)}")

        # Create standards report
        output_folder = "PIMMS v1.2/.temp"
        os.makedirs(output_folder, exist_ok=True)

        if final_report:
            matched_report_path = os.path.join(output_folder, "Standards_report.csv")
            pd.DataFrame(final_report).to_csv(matched_report_path, index=False)
            print(f"[DEBUG] Standards report saved to {matched_report_path}")

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
