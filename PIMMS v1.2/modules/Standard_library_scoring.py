import pandas as pd
import bisect


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
    """Load the PFAS primary standards library from a CSV file."""
    columns_to_read = [
        "PrecursorName",
        "PrecursorFormula",
        "PrecursorAdduct",
        "PrecursorCCS",
        "PrecursorRT",
        "PrecursorMz",
    ]
    return pd.read_csv(file_path, usecols=columns_to_read)


def load_external_targets_library(file_path):
    """Load the external targets library from an Excel file. Only uses m/z values."""
    return pd.read_excel(file_path, usecols=["PrecursorName", "PrecursorMz"])


def match_pfas_library(
    adjusted_df,
    pfas_library,
    file_path,
    standards_library_file,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=2.0,
    include_rt=True,
):
    """Matches features in adjusted_df with PFAS library entries based on mass, CCS, and RT."""
    matched_rows = []
    matched_ids = set()
    match_source = "PFAS Standards"

    sorted_pfas_masses = sorted(pfas_library["PrecursorMz"].tolist())

    for _, row in adjusted_df.iterrows():
        mz = row["m/z"]
        ccs = row["CCS"]
        rt = row["RT"] if include_rt else None

        matching_masses = find_similar_peaks(sorted_pfas_masses, mz, mass_error_ppm)

        for lib_mz in matching_masses:
            matching_rows = pfas_library[pfas_library["PrecursorMz"] == lib_mz]

            if matching_rows.empty:
                continue

            lib_row = matching_rows.iloc[0]

            mass_error = ((mz - lib_mz) / lib_mz) * 1e6
            ccs_error = (
                (ccs - lib_row["PrecursorCCS"]) / lib_row["PrecursorCCS"]
            ) * 100
            rt_error = (
                ((rt - lib_row["PrecursorRT"]) / lib_row["PrecursorRT"]) * 100
                if include_rt and pd.notna(rt) and pd.notna(lib_row["PrecursorRT"])
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
                    "Match": f"{lib_row['PrecursorName']} ({lib_row['PrecursorAdduct']})",
                    "Match Source": match_source,
                    "Classification Type": "likely",
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

    # Ensure 'Classification Type' is set for unmatched rows
    likely_unmatched_df["Match"] = "No Match"
    likely_unmatched_df["Match Source"] = "None"
    likely_unmatched_df["Classification Type"] = "unmatched"

    return likely_matched_df, likely_unmatched_df


def match_external_targets(unmatched_df, external_targets_library, mass_error_ppm=10):
    """Matches unmatched_df with External Targets library based on m/z only."""
    matched_rows = []
    matched_ids = set()
    match_source = "External Targets"

    sorted_external_masses = sorted(external_targets_library["PrecursorMz"].tolist())

    for _, row in unmatched_df.iterrows():
        mz = row["m/z"]

        matching_masses = find_similar_peaks(sorted_external_masses, mz, mass_error_ppm)

        for lib_mz in matching_masses:
            matching_rows = external_targets_library[
                external_targets_library["PrecursorMz"] == lib_mz
            ]

            if matching_rows.empty:
                continue

            lib_row = matching_rows.iloc[0]

            mass_error = ((mz - lib_mz) / lib_mz) * 1e6

            matched_ids.add(row["ID"])

            new_row = {
                "Match": f"{lib_row['PrecursorName']}",
                "Match Source": match_source,
                "Classification Type": "tentative",
                "ID": row["ID"],
                "RT": row["RT"],
                "DT": row["DT"],
                "CCS": row["CCS"],
                "m/z": row["m/z"],
                "Mass Error (ppm)": round(mass_error, 2),
                "CCS Error (%)": "N/A",
                "RT Error (%)": "N/A",
            }

            intensity_cols = {
                col: row[col] for col in unmatched_df.columns if ".d" in col
            }
            new_row.update(intensity_cols)

            matched_rows.append(new_row)

    external_matched_df = pd.DataFrame(matched_rows)
    external_unmatched_df = unmatched_df[~unmatched_df["ID"].isin(matched_ids)].copy()

    # Ensure 'Classification Type' is set for unmatched rows
    external_unmatched_df["Match"] = "No Match"
    external_unmatched_df["Match Source"] = "None"
    external_unmatched_df["Classification Type"] = "unmatched"

    return external_matched_df, external_unmatched_df


def main():
    # Example adjusted_df with rows to process
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [12.73, 3.5, 3.665, 3.666, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [203.65, 142.20, 147.02212060071, 175.79, 175.79],
            "m/z": [698.9155, 348.9398, 418.9734, 300, 400],
            "148 B2 16632.d.DeMP": [10, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [20, 20, 10, 10, 10],
        }
    )

    mass_error_ppm = 10
    rt_tolerance = 2.0
    ccs_tolerance = 2.0
    include_rt = False

    standards_library_file = (
        "PIMMS v1.2/import folder/Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    )
    external_targets_file = (
        "PIMMS v1.2/import folder/Kauffman_M-H_external_PFAS_library_mz_only.xlsx"
    )

    pfas_library = load_pfas_library(standards_library_file)
    external_targets_library = load_external_targets_library(external_targets_file)

    likely_matched_df, likely_unmatched_df = match_pfas_library(
        adjusted_df,
        pfas_library,
        standards_library_file,
        standards_library_file,
        mass_error_ppm,
        ccs_tolerance,
        rt_tolerance,
        include_rt,
    )

    external_matched_df, external_unmatched_df = match_external_targets(
        likely_unmatched_df, external_targets_library, mass_error_ppm
    )

    adjusted_df = pd.concat(
        [likely_matched_df, external_matched_df, external_unmatched_df],
        ignore_index=True,
    )

    print("\n[INFO] Likely Matched DF:")
    print(likely_matched_df)

    print("\n[INFO] External Matched DF:")
    print(external_matched_df)

    print("\n[INFO] External Unmatched DF:")
    print(external_unmatched_df)

    print("\n[INFO] Adjusted DF (Final):")
    print(adjusted_df)


if __name__ == "__main__":
    main()
