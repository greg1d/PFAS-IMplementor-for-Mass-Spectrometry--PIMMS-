import pandas as pd
import xml.etree.ElementTree as ET
import glob
import os
import bisect

# --- Data Extraction Functions (Unchanged) ---


def get_cef_sample_names(cef_folder):
    """
    Returns a list of sample names (without extension) from all `.cef` files in the folder.
    """
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    sample_names = [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]
    return sample_names


def parse_cef_file(cef_file_path):
    """
    Parses a .cef XML file and extracts peak information into a DataFrame.
    """
    tree = ET.parse(cef_file_path)
    root = tree.getroot()
    all_peaks = []
    compound_index = 1
    for compound in root.findall(".//Compound"):
        loc = compound.find("Location")
        if loc is None:
            continue
        rt = float(loc.attrib.get("rt", "nan"))
        ccs = float(loc.attrib.get("ccs", "nan"))
        dt = float(loc.attrib.get("dt", "nan"))
        peaks = compound.findall(".//MSPeaks/p")
        for peak in peaks:
            peak_data = {
                "Compound": compound_index,
                "RT": rt,
                "DT": dt,
                "CCS": ccs,
                "Peak_mz": float(peak.attrib.get("x", "nan")),
                "Peak_intensity": float(peak.attrib.get("y", "nan")),
            }
            all_peaks.append(peak_data)
        compound_index += 1
    df = pd.DataFrame(all_peaks)
    df["SourceFile"] = os.path.basename(cef_file_path)
    return df


def parse_all_cef_files_in_folder(cef_folder_path):
    """
    Finds all .cef files in a folder, parses each one, and returns a single combined DataFrame.
    """
    cef_files = glob.glob(os.path.join(cef_folder_path, "*.cef"))
    if not cef_files:
        raise FileNotFoundError(f"No .cef files found in folder: {cef_folder_path}")
    all_dataframes = [parse_cef_file(p) for p in cef_files]
    return pd.concat(all_dataframes, ignore_index=True)


def extract_multi_peak_compounds(cef_df):
    """Filters for compounds with more than one Peak_mz."""
    if cef_df.empty:
        return pd.DataFrame()
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    multi_peak_ids = peak_counts[peak_counts > 1].index
    return cef_df[cef_df["Compound"].isin(multi_peak_ids)].copy()


# --- Matching Algorithm Functions (Unchanged) ---


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, mass, mass_error_ppm=10):
    mass_bound = calculate_mass_error_no_charge(mass, mass_error_ppm)
    lower_bound = mass - mass_bound
    upper_bound = mass + mass_bound
    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    return array[j_start:j_end]


def match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm, sample_name):
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
                    "RT_PIMMS": pimms_row["RT"],
                    "RT_CEF": cef_row["RT"],
                    "CCS_PIMMS": pimms_row["CCS"],
                    "CCS_CEF": cef_row["CCS"],
                    "Peak_intensity": cef_row["Peak_intensity"],
                    sample_name: pimms_row[sample_name],
                    "Compound": cef_row["Compound"],
                }
                matched.append(merged_row)
    return pd.DataFrame(matched)


def filter_by_ccs_tolerance(mz_matched_df, ccs_tolerance_percent=2.0):
    if mz_matched_df.empty:
        return pd.DataFrame()
    percent_diff = (
        abs(mz_matched_df["CCS_PIMMS"] - mz_matched_df["CCS_CEF"])
        / mz_matched_df["CCS_PIMMS"]
        * 100
    )
    filtered_df = mz_matched_df[percent_diff <= ccs_tolerance_percent].copy()
    filtered_df["CCS_percent_diff"] = percent_diff[filtered_df.index]
    return filtered_df


# --- MODIFIED Pipeline and Reporting ---


def run_matching_pipeline(
    pimms_df,
    all_cef_data,
    sample_names,
    mass_error_ppm=5,
    ccs_tolerance=1,
    rt_tolerance=0.5,
):
    """
    Orchestrates the full matching pipeline and reports all associated CEF peaks for each match.
    """
    all_results = {}
    metadata_cols = ["CCS", "m/z", "RT", "DT", "ID"]

    for sample in sample_names:
        print(f"\n--- Processing Sample: {sample} ---")

        if sample not in pimms_df.columns:
            print(f"[SKIP] Sample '{sample}' not found in PIMMS data columns.")
            continue
        sample_pimms_df = pimms_df[metadata_cols + [sample]][pimms_df[sample] > 0]
        sample_cef_df = all_cef_data[all_cef_data["SourceFile"] == f"{sample}.cef"]

        multi_peak_cef_df = extract_multi_peak_compounds(sample_cef_df)
        print(
            f"[INFO] Found {multi_peak_cef_df['Compound'].nunique()} CEF compounds with >1 peak (out of {sample_cef_df['Compound'].nunique()} total)."
        )

        if sample_pimms_df.empty or multi_peak_cef_df.empty:
            print(
                f"[SKIP] No PIMMS data or no multi-peak CEF compounds for '{sample}'."
            )
            continue

        # --- Standard matching pipeline to find "anchor" hits ---
        mz_matches = match_pimms_to_cef_by_mz(
            sample_pimms_df, multi_peak_cef_df, mass_error_ppm, sample
        )
        if mz_matches.empty:
            print("[INFO] No m/z matches found.")
            continue

        ccs_filtered = filter_by_ccs_tolerance(mz_matches, ccs_tolerance)
        if ccs_filtered.empty:
            print(f"[INFO] No CCS matches within {ccs_tolerance}% tolerance.")
            continue

        rt_diff = abs(ccs_filtered["RT_PIMMS"] - ccs_filtered["RT_CEF"])
        rt_filtered_df = ccs_filtered[rt_diff <= rt_tolerance].copy()
        rt_filtered_df["RT_diff"] = rt_diff[rt_filtered_df.index]
        if rt_filtered_df.empty:
            print(f"[INFO] No RT matches within ±{rt_tolerance} min tolerance.")
            continue

        is_intensity_match = (
            rt_filtered_df[sample].round() == rt_filtered_df["Peak_intensity"].round()
        )
        anchor_matches_df = rt_filtered_df[is_intensity_match]

        if anchor_matches_df.empty:
            print("[INFO] No features survived the final intensity matching step.")
            continue

        # --- NEW: Generate the full compound report based on anchor hits ---

        # Get the unique compound IDs that had a successful match
        matched_compound_ids = anchor_matches_df["Compound"].unique()
        print(
            f"[SUCCESS] Found {len(anchor_matches_df)} anchor matches across {len(matched_compound_ids)} unique CEF compounds."
        )

        # Get the full peak list for these matched compounds
        full_compound_data = multi_peak_cef_df[
            multi_peak_cef_df["Compound"].isin(matched_compound_ids)
        ].copy()
        full_compound_data = full_compound_data.rename(
            columns={
                "RT": "CEF_RT",
                "CCS": "CEF_CCS",
                "Peak_mz": "CEF_Peak_mz",
                "Peak_intensity": "CEF_Peak_intensity",
                "DT": "CEF_DT",
            }
        )

        # Get the unique PIMMS anchor information that led to the match
        pimms_anchors = anchor_matches_df[
            ["PIMMS_m/z", "RT_PIMMS", "CCS_PIMMS", sample, "Compound"]
        ].drop_duplicates()

        # Join the PIMMS anchor info with the full CEF compound data
        final_report_df = pd.merge(
            pimms_anchors, full_compound_data, on="Compound", how="left"
        )

        all_results[sample] = final_report_df

    return all_results


def main():
    """
    Main function to load data and run the matching process.
    """
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    print("Loading PIMMS data...")
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = pimms_df.columns.str.strip()
    print("[INFO] Whitespace stripped from PIMMS column names.")

    print("Parsing all CEF files...")
    all_cef_data = parse_all_cef_files_in_folder(cef_folder)

    sample_names = get_cef_sample_names(cef_folder)

    final_results = run_matching_pipeline(
        pimms_df,
        all_cef_data,
        sample_names,
        mass_error_ppm=10,
        ccs_tolerance=2.0,
        rt_tolerance=1.0,
    )

    print(final_results)


if __name__ == "__main__":
    main()
