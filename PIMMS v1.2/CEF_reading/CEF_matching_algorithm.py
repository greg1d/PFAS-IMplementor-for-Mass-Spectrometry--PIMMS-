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
    Renames CCS fields for clarity.
    """
    cef_mz_array = sorted(cef_df["Peak_mz"].dropna().values)
    matched = []

    for _, pimms_row in pimms_df.iterrows():
        pimms_mz = pimms_row["m/z"]
        hits = find_similar_peaks(cef_mz_array, pimms_mz, mass_error_ppm)

        for cef_mz in hits:
            cef_matches = cef_df[cef_df["Peak_mz"] == cef_mz]
            for _, cef_row in cef_matches.iterrows():
                ppm_error = abs(pimms_mz - cef_mz) / pimms_mz * 1e6
                merged_row = {
                    "PIMMS_m/z": pimms_mz,
                    "CEF_Peak_mz": cef_mz,
                    "ppm_error": ppm_error,
                    "CCS_PIMMS": pimms_row["CCS"],
                    "CCS_CEF": cef_row["CCS"],
                    **pimms_row.to_dict(),
                    **cef_row.to_dict(),
                }
                matched.append(merged_row)

    return pd.DataFrame(matched)


def filter_by_ccs_tolerance(mz_matched_df, ccs_tolerance_percent=2.0):
    """
    Filters matches where CCS_CEF is within ±tolerance % of CCS_PIMMS.
    """
    filtered = []

    for _, row in mz_matched_df.iterrows():
        ccs_pimms = row.get("CCS_PIMMS")
        ccs_cef = row.get("CCS_CEF")

        if pd.notna(ccs_pimms) and pd.notna(ccs_cef):
            percent_diff = abs(ccs_pimms - ccs_cef) / ccs_pimms * 100
            if percent_diff <= ccs_tolerance_percent:
                row["CCS_percent_diff"] = percent_diff
                filtered.append(row)

    return pd.DataFrame(filtered)


def match_PIMMS_to_CEF(cef_folder, pimms_file, mass_error_ppm=10, ccs_tolerance=2.0):
    results = []

    for sample in get_cef_sample_names(cef_folder):
        pimms_df = extract_filtered_sample_data(sample, pimms_file)
        cef_df = parse_cef_file(get_cef_path(sample, cef_folder))

        if pimms_df.empty or cef_df.empty:
            print(f"[SKIP] No valid data for {sample}")
            continue

        mz_matches = match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm)
        if mz_matches.empty:
            print(f"[INFO] No m/z matches for {sample}")
            continue

        ccs_filtered = filter_by_ccs_tolerance(mz_matches, ccs_tolerance)
        if ccs_filtered.empty:
            print(f"[INFO] No CCS matches within {ccs_tolerance}% for {sample}")
            continue

        print(
            f"\n=== Final Matches for {sample} (±{mass_error_ppm} ppm, ±{ccs_tolerance}% CCS) ==="
        )
        print(
            ccs_filtered[
                [
                    "PIMMS_m/z",
                    "CEF_Peak_mz",
                    "ppm_error",
                    "CCS_PIMMS",
                    "CCS_CEF",
                    "CCS_percent_diff",
                ]
            ].to_string(index=False)
        )

        results.append((sample, ccs_filtered))

    return results


if __name__ == "__main__":
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set test.csv"
    match_PIMMS_to_CEF(cef_folder, pimms_file)
