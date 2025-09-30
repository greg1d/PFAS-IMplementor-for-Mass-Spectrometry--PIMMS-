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
    pfas_library,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=0.5,
    include_rt_scoring=True,
):
    """
    Matches features with a pre-standardized PFAS library DataFrame.
    Assumes the pfas_library DataFrame has columns named:
    'm/z', 'CCS', 'RT', 'Name', 'Adduct'.
    """
    # --- The entire "Validate the mapping and translate letters" block has been removed. ---

    # --- 1. Validate that the incoming library DataFrame has been standardized ---
    required_cols = {"m/z", "CCS", "RT", "Name", "Adduct"}
    if not required_cols.issubset(pfas_library.columns):
        missing = required_cols - set(pfas_library.columns)
        raise KeyError(
            f"Level 2 Library DataFrame is missing required standardized columns: {missing}"
        )

    # --- 2. Proceed with matching using direct column names ---
    matched_rows = []
    matched_ids = set()
    match_source = "PFAS Standards"

    sorted_pfas_masses = sorted(pfas_library["m/z"].tolist())

    for _, row in adjusted_df.iterrows():
        # Ensure the main dataframe also has the required columns
        mz = row["m/z"]
        ccs = row["CCS"]
        rt = row["RT"] if include_rt_scoring else None

        for lib_mz in find_similar_peaks(sorted_pfas_masses, mz, mass_error_ppm):
            matching_rows = pfas_library[pfas_library["m/z"] == lib_mz]
            if matching_rows.empty:
                continue
            lib_row = matching_rows.iloc[0]

            mass_error = ((mz - lib_mz) / lib_mz) * 1e6
            ccs_error = ((ccs - lib_row["CCS"]) / lib_row["CCS"]) * 100

            # --- RT Error logic corrected to use absolute difference ---
            rt_error = (
                abs(rt - lib_row["RT"])
                if include_rt_scoring and pd.notna(rt) and pd.notna(lib_row["RT"])
                else "N/A"
            )

            # Check if the feature is within all tolerances
            if -ccs_tolerance <= ccs_error <= ccs_tolerance:
                # --- RT check corrected to use absolute tolerance ---
                if (
                    include_rt_scoring
                    and isinstance(rt_error, (int, float))
                    and not (rt_error <= rt_tolerance)
                ):
                    continue
                if not (-mass_error_ppm <= mass_error <= mass_error_ppm):
                    continue

                matched_ids.add(row["ID"])

                new_row = {
                    # --- Use direct access with standard keys ---
                    "Match": f"{lib_row['Name']} ({lib_row['Adduct']})",
                    "Match Source": match_source,
                    "ID": row["ID"],
                    "RT": row["RT"],
                    "DT": row["DT"],
                    "CCS": row["CCS"],
                    "m/z": row["m/z"],
                    "Mass Error (ppm)": round(mass_error, 2),
                    "CCS Error (%)": round(ccs_error, 2),
                    # --- Output column name updated for clarity ---
                    "RT Error (abs)": round(rt_error, 2)
                    if isinstance(rt_error, (int, float))
                    else "N/A",
                }

                intensity_cols = {
                    col: row[col] for col in adjusted_df.columns if ".d" in col
                }
                new_row.update(intensity_cols)
                matched_rows.append(new_row)

    likely_matched_df = pd.DataFrame(matched_rows)
    likely_unmatched_df = adjusted_df[~adjusted_df["ID"].isin(matched_ids)].copy()

    likely_unmatched_df["Match"] = "No Match"
    likely_unmatched_df["Match Source"] = "None"
    likely_unmatched_df["Classification Type"] = "unmatched"

    return likely_matched_df, likely_unmatched_df


def level_5_library_matching(
    unmatched_df,
    external_targets_library,
    mass_error_ppm=10,
):
    """Matches unmatched_df with a pre-standardized external library."""
    matched_dict = {}
    matched_ids = set()
    match_source = "External Targets"

    # --- The entire "Translate library column letters" block has been removed. ---
    # We now assume 'external_targets_library' has columns named 'Name' and 'm/z'.

    # Ensure required columns exist in the pre-standardized library DataFrame
    required_cols = {"Name", "m/z"}
    if not required_cols.issubset(external_targets_library.columns):
        missing = required_cols - set(external_targets_library.columns)
        raise KeyError(
            f"Level 5 Library DataFrame is missing required standardized columns: {missing}"
        )

    # The rest of the function now uses direct column access
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

            if matching_rows.empty:
                continue

            for _, lib_row in matching_rows.iterrows():
                mass_error = ((mz - lib_mz) / lib_mz) * 1e6
                match_names.append(lib_row["Name"])  # Use direct column access
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
                "DT": row["DT"],
                "CCS": row["CCS"],
                "m/z": row["m/z"],
                "Mass Error (ppm)": ppm_str,
                "CCS Error (%)": "N/A",
                "RT Error (%)": "N/A",
            }

            intensity_cols = {
                col: row[col] for col in unmatched_df.columns if ".d" in col
            }
            new_row.update(intensity_cols)
            matched_dict[row["ID"]] = new_row

    external_matched_df = pd.DataFrame(matched_dict.values())
    external_unmatched_df = unmatched_df[~unmatched_df["ID"].isin(matched_ids)].copy()
    external_unmatched_df["Match"] = "No Match"
    external_unmatched_df["Match Source"] = "None"
    external_unmatched_df["Classification Type"] = "unmatched"

    return external_matched_df, external_unmatched_df
