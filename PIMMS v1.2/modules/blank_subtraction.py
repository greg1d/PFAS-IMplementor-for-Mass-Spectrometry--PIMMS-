import os

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
    This version dynamically identifies metadata columns.
    """
    all_columns = combined_data.columns.tolist()

    try:
        # --- Step 1: Define Control and Experimental Sample Columns ---
        control_start_index = column_letter_to_index(control_start_col)
        control_end_index = column_letter_to_index(control_end_col)
        control_samples = all_columns[control_start_index : control_end_index + 1]

        exp_start_index = column_letter_to_index(exp_start_col)
        exp_end_index = column_letter_to_index(exp_end_col)
        experimental_samples = all_columns[exp_start_index : exp_end_index + 1]

        # --- Step 2: Dynamically Identify Metadata Columns (The Fix) ---
        # A column is metadata if it's NOT a control or experimental sample.
        # We use a set for efficient lookup.
        data_columns_set = set(control_samples + experimental_samples)
        metadata_cols = [col for col in all_columns if col not in data_columns_set]

        # --- Step 3: Add Debug Statements and User Feedback ---
        print("--- Column Definition ---")

        # [DEBUG] New statement to show that metadata columns are correctly identified
        print(f"✔️ Dynamically identified metadata columns: {metadata_cols}")

        print(
            f"✔️ Control columns ('{control_start_col}' to '{control_end_col}') selected: {control_samples}"
        )
        print(
            f"✔️ Experimental columns ('{exp_start_col}' to '{exp_end_col}') selected: {experimental_samples}\n"
        )

        # --- Step 4: Create the Separate DataFrames ---
        # The logic here remains the same, but now uses the dynamically found metadata_cols
        control_df = combined_data[metadata_cols + control_samples]
        experimental_df = combined_data[metadata_cols + experimental_samples]

        return combined_data, control_df, experimental_df, metadata_cols

    except IndexError:
        raise ValueError(
            "A specified column letter is out of bounds for the data file. "
            f"The data has {len(all_columns)} columns."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to separate samples: {e}")


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


def method_1_blank_subtraction(
    control_df, experimental_df, metadata_cols, id_column="ID"
):
    """
    Subtracts the highest control value from the experimental samples for each row.

    This method first validates that the control and experimental dataframes are
    aligned using a specified ID column. It then dynamically identifies sample
    columns by excluding the provided metadata columns.

    Args:
        control_df (pd.DataFrame): DataFrame with metadata and control sample values.
        experimental_df (pd.DataFrame): DataFrame with metadata and experimental sample values.
        metadata_cols (list): A list of strings with the names of the metadata columns.
        id_column (str): The name of the column to use for row-wise alignment validation.

    Returns:
        tuple: A tuple containing:
            - adjusted_df (pd.DataFrame): Experimental data after blank subtraction.
            - control_mean (pd.Series): The mean of control values for each row.
            - control_std (pd.Series): The standard deviation of control values for each row.
    """
    # --- 1. Validation Step ---
    # Ensure the specified ID column exists and the DataFrames are perfectly aligned.
    if id_column not in control_df.columns or id_column not in experimental_df.columns:
        raise ValueError(
            f"The specified id_column '{id_column}' was not found in both DataFrames."
        )

    if not control_df[id_column].equals(experimental_df[id_column]):
        raise ValueError(
            f"The values in the '{id_column}' column do not match between the control and "
            "experimental DataFrames. Cannot perform row-wise subtraction on misaligned data."
        )

    print(
        f"✔️ Validation successful: '{id_column}' column is identical in both DataFrames."
    )

    # --- 2. Dynamically Identify Sample Columns ---
    # This avoids hardcoding positions with .iloc[]
    control_sample_cols = [
        col for col in control_df.columns if col not in metadata_cols
    ]
    exp_sample_cols = [
        col for col in experimental_df.columns if col not in metadata_cols
    ]

    print(f"Identified Control Sample Columns: {control_sample_cols}")
    print(f"Identified Experimental Sample Columns: {exp_sample_cols}")

    # --- 3. Perform Subtraction Logic ---
    # Calculate the maximum value in the control set for each row using column names
    control_max = control_df[control_sample_cols].max(axis=1)

    # Subtract the maximum control value from each row in the experimental set
    adjusted_values = experimental_df[exp_sample_cols].sub(control_max, axis=0)
    adjusted_values = adjusted_values.clip(lower=0)  # Ensure no negative values

    # Reconstruct the final DataFrame by combining metadata and adjusted values
    metadata_df = experimental_df[metadata_cols]
    adjusted_df = pd.concat([metadata_df, adjusted_values], axis=1)

    return adjusted_df


def method_2_blank_subtraction(
    control_df, experimental_df, metadata_cols, id_column="ID", std_deviation_factor=1
):
    """
    Subtracts the control mean plus a factor of the control standard deviation
    from the experimental samples for each row.

    This method first validates data alignment using an ID column, then dynamically
    identifies sample columns to perform the calculations.

    Args:
        control_df (pd.DataFrame): DataFrame with metadata and control sample values.
        experimental_df (pd.DataFrame): DataFrame with metadata and experimental sample values.
        metadata_cols (list): A list of strings with the names of the metadata columns.
        id_column (str): The name of the column to use for row-wise alignment validation.
        std_deviation_factor (float): Factor to multiply the standard deviation by before subtraction.

    Returns:
        tuple: A tuple containing:
            - adjusted_df (pd.DataFrame): Experimental data after subtraction.
            - control_mean (pd.Series): The mean of control values for each row.
            - control_std (pd.Series): The standard deviation of control values for each row.
    """
    # --- 1. Validation Step (replaces align_control_experimental) ---
    if id_column not in control_df.columns or id_column not in experimental_df.columns:
        raise ValueError(
            f"The specified id_column '{id_column}' was not found in both DataFrames."
        )

    if not control_df[id_column].equals(experimental_df[id_column]):
        raise ValueError(
            f"The values in the '{id_column}' column do not match. "
            "Cannot perform row-wise subtraction on misaligned data."
        )

    print(
        f"✔️ Validation successful: '{id_column}' column is identical in both DataFrames."
    )

    # --- 2. Dynamically Identify Sample Columns ---
    control_sample_cols = [
        col for col in control_df.columns if col not in metadata_cols
    ]
    exp_sample_cols = [
        col for col in experimental_df.columns if col not in metadata_cols
    ]

    print(f"Identified Control Sample Columns: {control_sample_cols}")
    print(f"Identified Experimental Sample Columns: {exp_sample_cols}")

    # --- 3. Perform Subtraction Logic using Pandas-native operations ---
    # Calculate row-wise mean and standard deviation for control samples
    control_mean = control_df[control_sample_cols].mean(axis=1)
    control_std = (
        control_df[control_sample_cols].std(axis=1).fillna(0)
    )  # fillna(0) for rows with one sample

    # Determine the total amount to subtract from each row
    subtraction_value = control_mean + (control_std * std_deviation_factor)

    # Subtract the calculated value from each experimental sample in the row
    experimental_values = experimental_df[exp_sample_cols]
    adjusted_values = experimental_values.sub(subtraction_value, axis=0)
    adjusted_values = adjusted_values.clip(lower=0)  # Ensure no negative values

    # --- 4. Reconstruct the DataFrame ---
    metadata_df = experimental_df[metadata_cols]
    adjusted_df = pd.concat([metadata_df, adjusted_values], axis=1)

    # --- 5. Return Consistent Tuple Output ---
    return adjusted_df, control_mean, control_std


# Replace the existing function in your modules/blank_subtraction.py file


def perform_blank_subtraction(
    method, control_df, experimental_df, metadata_cols, id_column="ID", std_devs=3.0
):
    """
    Performs blank subtraction by dispatching to the selected method.

    Args:
        method (str): The method number ('1' or '2').
        control_df (pd.DataFrame): DataFrame with control samples.
        experimental_df (pd.DataFrame): DataFrame with experimental samples.
        metadata_cols (list): List of metadata column names.
        id_column (str): The column name to use for alignment validation.
        std_devs (float): The number of standard deviations for Method 2.

    Returns:
        tuple: A tuple containing:
            - adjusted_df (pd.DataFrame): The blank-subtracted experimental data.
            - control_mean (pd.Series): The calculated mean of the control samples per row.
            - control_std (pd.Series): The calculated std dev of the control samples per row.
    """
    print(f"--- Performing Blank Subtraction using Method {method} ---")
    if method == "1":
        # Call Method 1 with the required metadata and ID column arguments
        adjusted_df, control_mean, control_std = method_1_blank_subtraction(
            control_df=control_df,
            experimental_df=experimental_df,
            metadata_cols=metadata_cols,
            id_column=id_column,
        )
        return adjusted_df, control_mean, control_std

    elif method == "2":
        # Call Method 2 with the required metadata and ID column arguments
        adjusted_df, control_mean, control_std = method_2_blank_subtraction(
            control_df=control_df,
            experimental_df=experimental_df,
            metadata_cols=metadata_cols,
            id_column=id_column,
            std_deviation_factor=std_devs,
        )
        return adjusted_df, control_mean, control_std

    else:
        raise ValueError("Invalid method selected. Please choose '1' or '2'.")
