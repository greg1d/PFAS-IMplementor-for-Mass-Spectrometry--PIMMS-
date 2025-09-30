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
    LEVEL_2_COLUMN_LETTERS,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=2.0,
    include_rt=True,
):
    """
    Matches features with PFAS library entries using user-defined column letters for the library.
    """
    # --- 1. Validate the mapping and translate letters to column names ---
    required_keys = {"m/z", "CCS", "RT", "Name", "Adduct"}
    if not required_keys.issubset(LEVEL_2_COLUMN_LETTERS.keys()):
        missing_keys = required_keys - set(LEVEL_2_COLUMN_LETTERS.keys())
        raise KeyError(
            f"Configuration is missing required library column keys: {missing_keys}"
        )

    lib_cols = {}
    all_lib_columns = pfas_library.columns.tolist()
    print(all_lib_columns)
    for key, letter in LEVEL_2_COLUMN_LETTERS.items():
        try:
            index = column_letter_to_index(letter)
            if index >= len(all_lib_columns):
                raise IndexError(
                    f"Column '{letter}' is out of bounds for the library file."
                )
            lib_cols[key] = all_lib_columns[index]
        except Exception as e:
            raise ValueError(
                f"Could not process library mapping for '{key}' ('{letter}'): {e}"
            )

    # --- 2. Proceed with matching ---
    matched_rows = []
    matched_ids = set()
    match_source = "PFAS Standards"

    sorted_pfas_masses = sorted(pfas_library[lib_cols["m/z"]].tolist())

    for _, row in adjusted_df.iterrows():
        mz = row["m/z"]
        ccs = row["CCS"]
        rt = row["RT"] if include_rt else None

        for lib_mz in find_similar_peaks(sorted_pfas_masses, mz, mass_error_ppm):
            matching_rows = pfas_library[pfas_library[lib_cols["m/z"]] == lib_mz]
            if matching_rows.empty:
                continue
            lib_row = matching_rows.iloc[0]

            mass_error = ((mz - lib_mz) / lib_mz) * 1e6
            ccs_error = (
                (ccs - lib_row[lib_cols["CCS"]]) / lib_row[lib_cols["CCS"]]
            ) * 100
            rt_error = (
                ((rt - lib_row[lib_cols["RT"]]) / lib_row[lib_cols["RT"]]) * 100
                if include_rt and pd.notna(rt) and pd.notna(lib_row[lib_cols["RT"]])
                else "N/A"
            )

            if -ccs_tolerance <= ccs_error <= ccs_tolerance:
                if (
                    include_rt
                    and isinstance(rt_error, (int, float))
                    and not (-rt_tolerance <= rt_error <= rt_tolerance)
                ):
                    continue
                if not (-mass_error_ppm <= mass_error <= mass_error_ppm):
                    continue

                matched_ids.add(row["ID"])

                new_row = {
                    "Match": f"{lib_row[lib_cols['name']]} ({lib_row[lib_cols['adduct']]})",
                    "Match Source": match_source,
                    "ID": row["ID"],
                    "RT": row["RT"],
                    "DT": row["DT"],
                    "CCS": row["CCS"],
                    "m/z": row["m/z"],
                    "Mass Error (ppm)": round(mass_error, 2),
                    "CCS Error (%)": round(ccs_error, 2),
                    "RT Error (%)": round(rt_error, 2)
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
    library_column_letters,  # <-- New parameter for letter mapping
    mass_error_ppm=10,
):
    """Matches unmatched_df with an external library using user-defined column letters."""
    matched_dict = {}
    matched_ids = set()
    match_source = "External Targets"

    # --- Translate library column letters to actual column names ---
    required_keys = {"Name", "m/z"}
    if not required_keys.issubset(library_column_letters.keys()):
        missing_keys = required_keys - set(library_column_letters.keys())
        raise KeyError(
            f"Configuration is missing required library column keys: {missing_keys}"
        )

    lib_cols = {}
    all_lib_columns = external_targets_library.columns.tolist()
    for key, letter in library_column_letters.items():
        try:
            index = column_letter_to_index(letter)
            if index >= len(all_lib_columns):
                raise IndexError(
                    f"Column '{letter}' is out of bounds for the library file."
                )
            lib_cols[key] = all_lib_columns[index]
        except Exception as e:
            raise ValueError(
                f"Could not process library mapping for '{key}' ('{letter}'): {e}"
            )
    # --- End of translation section ---

    # The rest of the function now uses the dynamically found column names
    numeric_mz = pd.to_numeric(
        external_targets_library[lib_cols["m/z"]], errors="coerce"
    )
    sorted_external_masses = sorted(numeric_mz.dropna().tolist())
    for _, row in unmatched_df.iterrows():
        mz = row["m/z"]
        match_names = []
        ppm_errors = []

        matching_masses = find_similar_peaks(sorted_external_masses, mz, mass_error_ppm)

        for lib_mz in matching_masses:
            matching_rows = external_targets_library[
                external_targets_library[lib_cols["m/z"]] == lib_mz
            ]

            if matching_rows.empty:
                continue

            for _, lib_row in matching_rows.iterrows():
                mass_error = ((mz - lib_mz) / lib_mz) * 1e6
                match_names.append(lib_row[lib_cols["Name"]])  # Use mapped name column
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
