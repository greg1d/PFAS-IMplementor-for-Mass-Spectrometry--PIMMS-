import bisect

import pandas as pd


def calculate_mass_error_no_charge(mass, mass_error_ppm=10):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, mass, mass_error_ppm=10):
    """Finds peaks within the mass error bounds using binary search."""
    mass_bound = calculate_mass_error_no_charge(mass, mass_error_ppm)
    lower_bound = mass - mass_bound
    upper_bound = mass + mass_bound

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)

    return array[j_start:j_end]


def load_pfas_library(file_path):
    """
    Load specific columns from the PFAS primary standards library.

    Args:
        file_path (str): The path to the CSV library file.
        columns_to_load (list): A list of column names to load from the file.

    Returns:
        pd.DataFrame: A DataFrame containing only the specified columns.
    """
    try:
        # The 'sep' argument is added in case the file is tab-separated
        return pd.read_csv(file_path)
    except ValueError as e:
        # This error occurs if a column in 'usecols' is not in the file
        print(
            f"[ERROR] Could not load PFAS library. Check if all specified columns exist in '{file_path}'."
        )
        raise e
    except FileNotFoundError:
        print(f"[ERROR] PFAS library file not found at: '{file_path}'")
        raise


# This helper function is required
def column_letter_to_index(letter):
    """Converts an Excel-style column letter to a zero-based integer index."""
    letter = letter.upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def level_2_library_matching(
    adjusted_df,
    metadata_cols,
    pfas_library,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=0.5,
    include_rt_scoring=True,
):
    """
    Matches features with a standardized library, using a metadata list to
    identify sample columns. Assumes 'adjusted_df' contains standardized columns:
    'ID', 'RT', 'm/z', 'CCS', and 'DT'.
    """
    if adjusted_df.empty:
        print("[INFO] No features to process for Level 2 matching.")
        return pd.DataFrame(), pd.DataFrame()

    # --- 1. Validate the external library DataFrame ---
    required_lib_cols = {"m/z", "CCS", "RT", "Name", "Adduct"}
    if not required_lib_cols.issubset(pfas_library.columns):
        missing = required_lib_cols - set(pfas_library.columns)
        raise KeyError(
            f"Level 2 Library DataFrame is missing required standardized columns: {missing}"
        )

    # --- 2. Robustly identify sample columns by excluding metadata ---
    intensity_cols = [col for col in adjusted_df.columns if col not in metadata_cols]

    # --- 3. Perform Matching ---
    matched_rows = []
    matched_ids = set()
    match_source = "CCS Library"
    sorted_pfas_masses = sorted(pfas_library["m/z"].tolist())

    for _, row in adjusted_df.iterrows():
        mz = row["m/z"]
        ccs = row["CCS"]
        rt = row["RT"] if include_rt_scoring else None

        for lib_mz in find_similar_peaks(sorted_pfas_masses, mz, mass_error_ppm):
            lib_row = pfas_library[pfas_library["m/z"] == lib_mz].iloc[0]

            mass_error = ((mz - lib_mz) / lib_mz) * 1e6
            ccs_error = ((ccs - lib_row["CCS"]) / lib_row["CCS"]) * 100
            rt_error = (
                abs(rt - lib_row["RT"])
                if include_rt_scoring and pd.notna(rt) and pd.notna(lib_row["RT"])
                else "N/A"
            )

            # Check if the feature is within all tolerances
            rt_match = not (
                isinstance(rt_error, (int, float)) and rt_error > rt_tolerance
            )
            ccs_match = -ccs_tolerance <= ccs_error <= ccs_tolerance

            if ccs_match and rt_match:
                matched_ids.add(row["ID"])

                new_row = {
                    "Match": f"{lib_row['Name']} ({lib_row['Adduct']})",
                    "Match Source": match_source,
                    "ID": row["ID"],
                    "RT": row["RT"],
                    "DT": row.get("DT"),  # Use .get() for optional 'DT' column
                    "CCS": row["CCS"],
                    "m/z": row["m/z"],
                    "Mass Error (ppm)": round(mass_error, 2),
                    "CCS Error (%)": round(ccs_error, 2),
                    "RT Error (abs)": (
                        round(rt_error, 2)
                        if isinstance(rt_error, (int, float))
                        else "N/A"
                    ),
                }

                # Add all intensity columns with their values
                for col in intensity_cols:
                    new_row[col] = row[col]

                matched_rows.append(new_row)

    # --- 4. Assemble Final DataFrames ---
    matched_df = pd.DataFrame(matched_rows)
    unmatched_df = adjusted_df[~adjusted_df["ID"].isin(matched_ids)].copy()

    unmatched_df["Match"] = "No Match"
    unmatched_df["Match Source"] = "None"

    # Define a consistent final column order
    output_cols_front = [
        "Match",
        "Match Source",
        "ID",
        "RT",
        "DT",
        "CCS",
        "m/z",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (abs)",
    ]

    # Ensure both dataframes have the same final columns for easy concatenation later
    final_cols = output_cols_front + intensity_cols

    # Re-order and add missing columns filled with None/NaN
    if not matched_df.empty:
        matched_df = matched_df.reindex(columns=final_cols)
    if not unmatched_df.empty:
        unmatched_df = unmatched_df.reindex(columns=final_cols)

    # Add classification type to unmatched
    unmatched_df["Classification Type"] = "unmatched"

    return matched_df, unmatched_df


# Assuming find_similar_peaks is available from another module in your project
# from .helpers import find_similar_peaks


def level_5_library_matching(
    unmatched_df,
    metadata_cols,
    external_targets_library,
    mass_error_ppm=10,
):
    """
    [MODIFIED] Matches features with an external target list, robustly identifying sample columns.
    """
    if unmatched_df.empty:
        print("[INFO] No unmatched features to process for Level 5 matching.")
        return pd.DataFrame(), unmatched_df

    # --- 1. Validate the external library DataFrame ---
    required_lib_cols = {"Name", "m/z"}
    if not required_lib_cols.issubset(external_targets_library.columns):
        missing = required_lib_cols - set(external_targets_library.columns)
        raise KeyError(
            f"Level 5 Library DataFrame is missing required standardized columns: {missing}"
        )

    # --- 2. Robustly identify sample columns by excluding metadata ---
    sample_cols = [col for col in unmatched_df.columns if col not in metadata_cols]

    # --- 3. Perform Matching ---
    matched_dict = {}
    matched_ids = set()
    match_source = "Suspects Library"
    numeric_mz = pd.to_numeric(external_targets_library["m/z"], errors="coerce")
    sorted_external_masses = sorted(numeric_mz.dropna().tolist())

    for _, row in unmatched_df.iterrows():
        mz = row["m/z"]
        match_names = []
        ppm_errors = []

        matching_masses = find_similar_peaks(sorted_external_masses, mz, mass_error_ppm)

        for lib_mz in matching_masses:
            matching_rows = external_targets_library[
                external_targets_library["m/z"] == lib_mz
            ]
            for _, lib_row in matching_rows.iterrows():
                mass_error = ((mz - lib_mz) / lib_mz) * 1e6
                match_names.append(lib_row["Name"])
                ppm_errors.append(str(round(mass_error, 2)))
                matched_ids.add(row["ID"])

        if match_names:
            match_str = " or ".join(sorted(set(match_names)))
            ppm_str = " or ".join(sorted(set(ppm_errors), key=float))

            new_row = {
                "Match": match_str,
                "Match Source": match_source,
                "Classification Type": "tentative",
                "ID": row["ID"],
                "RT": row["RT"],
                "DT": row.get("DT"),
                "CCS": row["CCS"],
                "m/z": row["m/z"],
                "Mass Error (ppm)": ppm_str,
                "CCS Error (%)": "N/A",
                "RT Error (abs)": "N/A",  # Changed name for consistency
            }

            # Add all sample columns with their values using the robust list
            for col in sample_cols:
                new_row[col] = row[col]

            matched_dict[row["ID"]] = new_row

    # --- 4. Assemble Final DataFrames ---
    external_matched_df = pd.DataFrame(matched_dict.values())
    external_unmatched_df = unmatched_df[~unmatched_df["ID"].isin(matched_ids)].copy()

    # Define a consistent final column order
    output_cols_front = [
        "Match",
        "Match Source",
        "Classification Type",
        "ID",
        "RT",
        "DT",
        "CCS",
        "m/z",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (abs)",
    ]
    final_cols = output_cols_front + sample_cols

    # Re-order and add missing columns filled with None/NaN
    if not external_matched_df.empty:
        external_matched_df = external_matched_df.reindex(columns=final_cols)
    if not external_unmatched_df.empty:
        external_unmatched_df = external_unmatched_df.reindex(columns=final_cols)

    return external_matched_df, external_unmatched_df
