from CEF_PIMMS_matcher import (
    get_cef_sample_names,
    extract_filtered_sample_data,
    get_cef_path,
    parse_cef_file,
)
import pandas as pd
import bisect
import xml.etree.ElementTree as ET
import os


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


def match_PIMMS_to_CEF(
    cef_folder, pimms_file, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=1.0
):
    results = []

    for sample in get_cef_sample_names(cef_folder):
        pimms_df = extract_filtered_sample_data(sample, pimms_file)
        cef_df = parse_cef_file(get_cef_path(sample, cef_folder))

        if pimms_df.empty or cef_df.empty:
            print(f"[SKIP] No valid data for {sample}")
            continue

        # Rename RT columns
        pimms_df = pimms_df.rename(columns={"RT": "RT_PIMMS"})
        cef_df = cef_df.rename(columns={"RT": "RT_CEF"})

        # Step 1: m/z match
        mz_matches = match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm)
        if mz_matches.empty:
            print(f"[INFO] No m/z matches for {sample}")
            continue

        # Step 2: CCS match
        ccs_filtered = filter_by_ccs_tolerance(mz_matches, ccs_tolerance)
        if ccs_filtered.empty:
            print(f"[INFO] No CCS matches within {ccs_tolerance}% for {sample}")
            continue

        # Step 3: RT match
        rt_filtered = []
        for _, row in ccs_filtered.iterrows():
            rt_pimms = row.get("RT_PIMMS")
            rt_cef = row.get("RT_CEF")
            if pd.notna(rt_pimms) and pd.notna(rt_cef):
                rt_diff = abs(rt_pimms - rt_cef)
                if rt_diff <= rt_tolerance:
                    row["RT_diff"] = rt_diff
                    rt_filtered.append(row)

        if not rt_filtered:
            print(f"[INFO] No RT matches within ±{rt_tolerance} min for {sample}")
            continue

        rt_df = pd.DataFrame(rt_filtered)

        # Step 4: Intensity match
        intensity_matched = []
        for _, row in rt_df.iterrows():
            pimms_intensity = row[sample]
            cef_intensity = row.get("Peak_intensity")

            if pd.notna(pimms_intensity) and pd.notna(cef_intensity):
                pimms_rounded = round(pimms_intensity)  # <-- force integer rounding
                cef_rounded = round(cef_intensity)

                if pimms_rounded == cef_rounded:
                    intensity_matched.append(row)

        final_df = pd.DataFrame(intensity_matched)

        final_df[
            [
                "PIMMS_m/z",
                "CEF_Peak_mz",
                "ppm_error",
                "CCS_PIMMS",
                "CCS_CEF",
                "CCS_percent_diff",
                "RT_PIMMS",
                "RT_CEF",
                "RT_diff",
                "Peak_intensity",
                sample,
                "Compound",
            ]
        ].to_string(index=False)

        results.append((sample, final_df))

    return results


def compound_lookup(sample_name, cef_folder, compound_id):
    """
    Looks up and prints all peak-level information for a given compound ID
    in the CEF file corresponding to the sample.
    """
    cef_file = os.path.join(cef_folder, sample_name + ".cef")
    if not os.path.exists(cef_file):
        print(f"[ERROR] CEF file not found for sample: {sample_name}")
        return

    tree = ET.parse(cef_file)
    root = tree.getroot()

    all_peaks = []
    compound_index = 1

    for compound in root.findall(".//Compound"):
        if compound_index != compound_id:
            compound_index += 1
            continue

        loc = compound.find("Location")
        if loc is None:
            print(f"[WARN] Compound {compound_id} has no location tag.")
            return

        rt = float(loc.attrib.get("rt", "nan"))
        dt = float(loc.attrib.get("dt", "nan"))
        ccs = float(loc.attrib.get("ccs", "nan"))

        peaks = compound.findall(".//MSPeaks/p")
        peak_mzs = [float(p.attrib.get("x", "nan")) for p in peaks]
        min_peak_mz = min(peak_mzs) if peak_mzs else float("nan")

        for peak in peaks:
            peak_data = {
                "Compound": compound_index,
                "RT": rt,
                "DT": dt,
                "CCS": ccs,
                "Peak_mz": float(peak.attrib.get("x", "nan")),
                "m/z": min_peak_mz,
                "Peak_intensity": float(peak.attrib.get("y", "nan")),
            }
            all_peaks.append(peak_data)

        break  # Stop after finding the compound

    if not all_peaks:
        print(f"[INFO] No peaks found for Compound {compound_id} in {sample_name}")
        return

    peaks_df = pd.DataFrame(all_peaks)

    return peaks_df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    mass_error_ppm = 10
    ccs_tolerance = 2.0
    rt_tolerance = 1.0

    matches = match_PIMMS_to_CEF(
        cef_folder=cef_folder,
        pimms_file=pimms_file,
        mass_error_ppm=mass_error_ppm,
        ccs_tolerance=ccs_tolerance,
        rt_tolerance=rt_tolerance,
    )

    for sample_name, match_df in matches:
        for compound_id in match_df["Compound"].unique():
            compound_lookup(sample_name, cef_folder, int(compound_id))


if __name__ == "__main__":
    main()
