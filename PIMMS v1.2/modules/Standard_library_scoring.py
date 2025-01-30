import pandas as pd
import bisect
import os


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
    """Load the PFAS library from a CSV file."""
    columns_to_read = [
        "PrecursorName",
        "PrecursorFormula",
        "PrecursorAdduct",
        "PrecursorCCS",
        "PrecursorRT",
        "PrecursorMz",
    ]
    return pd.read_csv(file_path, usecols=columns_to_read)


def match_pfas_library(
    adjusted_df,
    pfas_library,
    file_path,
    standards_library_file,
    mass_error_ppm=10,
    ccs_tolerance=2.0,  # Now set from -2% to +2%
    rt_tolerance=0.5,  # Absolute tolerance for RT
    include_rt=True,
):
    """Matches features in adjusted_df with PFAS library entries based on mass (ppm), CCS (%), and optionally RT."""
    matched_rows = []
    matched_ids = set()  # Store IDs of matched features

    # Extract only the filename without the path or extension
    match_source = os.path.basename(file_path).replace(".csv", "")

    # Sort PFAS library by mass for efficient binary search
    sorted_pfas_masses = sorted(pfas_library["PrecursorMz"].tolist())

    for _, row in adjusted_df.iterrows():
        mz = row["m/z"]
        ccs = row["CCS"]
        rt = row["RT"] if include_rt else None

        # Get mass-matched peaks
        matching_masses = find_similar_peaks(sorted_pfas_masses, mz, mass_error_ppm)

        for lib_mz in matching_masses:
            lib_row = pfas_library[pfas_library["PrecursorMz"] == lib_mz].iloc[0]

            lib_ccs = lib_row["PrecursorCCS"]
            lib_rt = lib_row["PrecursorRT"] if include_rt else None

            # Calculate errors
            mass_error = ((mz - lib_mz) / lib_mz) * 1e6  # ppm error
            ccs_error = ((ccs - lib_ccs) / lib_ccs) * 100  # % error
            rt_error = (
                (rt - lib_rt) if include_rt else None
            )  # Absolute error in minutes

            # Check if within CCS tolerance (-2% to +2%)
            if -ccs_tolerance <= ccs_error <= ccs_tolerance:
                if include_rt and abs(rt_error) > rt_tolerance:
                    continue  # Skip if RT is out of tolerance

                # Store ID of matched feature
                matched_ids.add(row["ID"])

                # Determine classification type
                classification_type = (
                    "likely" if file_path == standards_library_file else "tentative"
                )

                # Append match details
                match_str = f"{lib_row['PrecursorName']} ({lib_row['PrecursorAdduct']})"
                new_row = {
                    "Match": match_str,
                    "Match Source": match_source,
                    "Classification Type": classification_type,
                    "ID": row["ID"],
                    "RT": row["RT"],
                    "DT": row["DT"],
                    "CCS": row["CCS"],
                    "m/z": row["m/z"],
                    "Mass Error (ppm)": round(mass_error, 2),
                    "CCS Error (%)": round(ccs_error, 2),
                    "RT Error (min)": round(rt_error, 2) if include_rt else "N/A",
                }

                # Include intensity columns (.d)
                intensity_cols = {
                    col: row[col] for col in adjusted_df.columns if ".d" in col
                }
                new_row.update(intensity_cols)

                matched_rows.append(new_row)

    # Create matched DataFrame (Ensuring structure even if empty)
    column_order = [
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
        "RT Error (min)",
    ]
    intensity_cols = [col for col in adjusted_df.columns if ".d" in col]
    column_order.extend(intensity_cols)

    matched_df = pd.DataFrame(matched_rows, columns=column_order).fillna("N/A")

    # Create unmatched DataFrame (features not found in standards library)
    unmatched_df = adjusted_df[~adjusted_df["ID"].isin(matched_ids)].copy()

    # Ensure unmatched_df has the same columns as matched_df
    for col in column_order:
        if col not in unmatched_df.columns:
            unmatched_df[col] = "N/A"

    unmatched_df = unmatched_df[column_order]  # Reorder columns

    return matched_df, unmatched_df


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
    rt_tolerance = 0.5
    ccs_tolerance = 2.0  # -2% to +2% tolerance
    include_rt = True

    # Define standards library file path
    standards_library_file = (
        "PIMMS v1.2/import folder/Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    )

    # Load PFAS library
    pfas_library = load_pfas_library(standards_library_file)

    # Match PFAS library and get matched/unmatched data
    matched_df, unmatched_df = match_pfas_library(
        adjusted_df,
        pfas_library,
        standards_library_file,
        standards_library_file,
        mass_error_ppm,
        ccs_tolerance,
        rt_tolerance,
        include_rt,
    )

    # Combine matched and unmatched for adjusted_df
    adjusted_df = pd.concat([matched_df, unmatched_df], ignore_index=True)

    print("\n[INFO] Matched DataFrame:")
    print(matched_df)

    print("\n[INFO] Unmatched DataFrame:")
    print(unmatched_df)

    print("\n[INFO] Adjusted DataFrame (Matched + Unmatched):")
    print(adjusted_df)


if __name__ == "__main__":
    main()
