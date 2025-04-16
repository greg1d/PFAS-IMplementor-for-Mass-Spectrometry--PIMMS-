from CEF_PIMMS_matcher import (
    get_cef_sample_names,
    extract_filtered_sample_data,
    get_cef_path,
    parse_cef_file,
)
import pandas as pd
import bisect


def calculate_mass_error_no_charge(mass, mass_error_ppm):
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


def match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm):
    """
    Matches each PIMMS 'm/z' to CEF 'Peak_mz' using binary search with ±ppm.
    Returns a merged DataFrame with match information.
    """
    cef_mz_array = sorted(cef_df["Peak_mz"].dropna().values)
    matched = []

    for _, pimms_row in pimms_df.iterrows():
        pimms_mz = pimms_row["m/z"]
        hits = find_similar_peaks(cef_mz_array, pimms_mz, mass_error_ppm)

        for cef_mz in hits:
            # Get matching row(s) from cef_df
            cef_matches = cef_df[cef_df["Peak_mz"] == cef_mz]
            for _, cef_row in cef_matches.iterrows():
                ppm_error = abs(pimms_mz - cef_mz) / pimms_mz * 1e6
                merged_row = {
                    "PIMMS_m/z": pimms_mz,
                    "CEF_Peak_mz": cef_mz,
                    "ppm_error": ppm_error,
                    **pimms_row.to_dict(),
                    **cef_row.to_dict(),
                }
                matched.append(merged_row)

    return pd.DataFrame(matched)


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set test.csv"
    mass_error_ppm = 10

    sample_names = get_cef_sample_names(cef_folder)
    print(f"[INFO] Found {len(sample_names)} .cef files.")

    for sample_name in sample_names:
        # Extract data
        pimms_df = extract_filtered_sample_data(sample_name, pimms_file_path)
        cef_path = get_cef_path(sample_name, cef_folder)
        cef_df = parse_cef_file(cef_path)

        if pimms_df is not None and not pimms_df.empty and not cef_df.empty:
            matches_df = match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm)

            print(f"\n=== Matched Features for Sample: {sample_name} ===")
            if not matches_df.empty:
                print(
                    matches_df[["PIMMS_m/z", "CEF_Peak_mz", "ppm_error"]].to_string(
                        index=False
                    )
                )
            else:
                print("No matches found within tolerance.")
        else:
            print(f"[SKIP] No valid data to match for {sample_name}")


if __name__ == "__main__":
    main()
