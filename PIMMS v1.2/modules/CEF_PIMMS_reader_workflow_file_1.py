import bisect
import glob
import os
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

# --- Data Extraction and Calculation Functions ---


def get_cef_sample_names(cef_folder):
    """Returns a list of sample names from .cef files."""
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    print(f"DEBUG: Found {len(cef_files)} .cef files in {cef_folder}")
    # Extract just the filename without extension
    sample_names = [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]
    return sample_names


def parse_cef_file(cef_file_path):
    """Parses a .cef XML file."""
    try:
        tree = ET.parse(cef_file_path)
        root = tree.getroot()
        all_peaks = []
        compound_index = 1
        for compound in root.findall(".//Compound"):
            loc = compound.find("Location")
            if loc is None:
                continue
            rt, ccs, dt = (
                float(loc.attrib.get("rt", "nan")),
                float(loc.attrib.get("ccs", "nan")),
                float(loc.attrib.get("dt", "nan")),
            )
            for peak in compound.findall(".//MSPeaks/p"):
                all_peaks.append(
                    {
                        "Compound": compound_index,
                        "RT": rt,
                        "DT": dt,
                        "CCS": ccs,
                        "Peak_mz": float(peak.attrib.get("x", "nan")),
                        "Peak_intensity": float(peak.attrib.get("y", "nan")),
                    }
                )
            compound_index += 1
        df = pd.DataFrame(all_peaks)
        df["SourceFile"] = os.path.basename(cef_file_path)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to parse {cef_file_path}: {e}")
        return pd.DataFrame()


def parse_all_cef_files_in_folder(cef_folder_path):
    """Parses all .cef files in a given folder."""
    cef_files = glob.glob(os.path.join(cef_folder_path, "*.cef"))
    if not cef_files:
        raise FileNotFoundError(f"No .cef files found in folder: {cef_folder_path}")

    print(f"[INFO] Parsing {len(cef_files)} CEF files...")
    all_dfs = []
    for p in cef_files:
        df = parse_cef_file(p)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)


def compute_kaufman_constants(cef_data_df):
    """Computes Kaufman C and extracts intensities for the first 3 peaks."""
    # print("[DEBUG] Computing Kaufman constants...")
    kaufman_data = []
    grouped = cef_data_df.groupby(["SourceFile", "Compound"])

    for (source_file, compound_id), group in grouped:
        if len(group) < 2:
            continue

        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]

        intensity3 = np.nan
        if len(sorted_group) >= 3:
            intensity3 = sorted_group.loc[2, "Peak_intensity"]

        if intensity1 == 0:
            continue

        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)

        if kaufman_C == 0:
            continue

        # Mass defect calculation
        mass_defect = mz1 - round(mz1)

        sample_name = os.path.splitext(source_file)[0].strip()

        kaufman_data.append(
            {
                "Sample": sample_name,
                "Compound": compound_id,
                "Peak_mz_1": mz1,
                "Intensity_1": intensity1,
                "Peak_mz_2": sorted_group.loc[1, "Peak_mz"],
                "Intensity_2": intensity2,
                "Intensity_3": intensity3,
                "Kaufman_C": kaufman_C,
                "m_over_C": mz1 / kaufman_C,
                "mass_defect": mass_defect,
                "md_over_C": mass_defect / kaufman_C,
            }
        )
    return pd.DataFrame(kaufman_data)


def extract_multi_peak_compounds(cef_df):
    if cef_df.empty:
        return pd.DataFrame()
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    return cef_df[cef_df["Compound"].isin(peak_counts[peak_counts > 1].index)].copy()


def find_similar_peaks(array, mass, mass_error_ppm=10):
    mass_bound = mass * mass_error_ppm * 1e-6
    return array[
        bisect.bisect_left(array, mass - mass_bound) : bisect.bisect_right(
            array, mass + mass_bound
        )
    ]


def filter_by_ccs_tolerance(df, tol=2.0):
    if df.empty:
        return pd.DataFrame()
    diff = abs(df["CCS_PIMMS"] - df["CCS_CEF"]) / df["CCS_PIMMS"] * 100
    fdf = df[diff <= tol].copy()
    fdf["CCS_percent_diff"] = diff[fdf.index]
    return fdf


def match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm, sample_name):
    cef_mz_array, matched = sorted(cef_df["Peak_mz"].dropna().values), []
    for _, prow in pimms_df.iterrows():
        hits = find_similar_peaks(cef_mz_array, prow["m/z"], mass_error_ppm)
        for cef_mz in hits:
            for _, crow in cef_df[cef_df["Peak_mz"] == cef_mz].iterrows():
                match_data = {
                    "PIMMS_m/z": prow["m/z"],
                    "CEF_Peak_mz": cef_mz,
                    "ppm_error": abs(prow["m/z"] - cef_mz) / prow["m/z"] * 1e6,
                    "RT_PIMMS": prow["RT"],
                    "RT_CEF": crow["RT"],
                    "CCS_PIMMS": prow["CCS"],
                    "CCS_CEF": crow["CCS"],
                    "DT_PIMMS": prow["DT"],
                    "Peak_intensity": crow["Peak_intensity"],
                    sample_name: prow[sample_name],
                    "Compound": crow["Compound"],
                    "Match_ID": prow.get("Match", "N/A"),
                    "Classification Type": prow.get("Classification Type", "N/A"),
                }
                matched.append(match_data)
    return pd.DataFrame(matched)


def run_matching_pipeline(
    pimms_df,
    all_cef_data,
    sample_names,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=1.0,
):
    print(
        f"\n[DEBUG] Pipeline started. Scanning for {len(sample_names)} potential samples from CEF files..."
    )

    all_results_list = []
    metadata_cols = ["CCS", "m/z", "RT", "DT", "ID", "Match", "Classification Type"]

    for cef_name in sample_names:
        # --- ROBUST COLUMN MATCHING ---
        matched_col = None
        if cef_name in pimms_df.columns:
            matched_col = cef_name
        else:
            for col in pimms_df.columns:
                if cef_name in col:
                    matched_col = col
                    break

        if not matched_col:
            print(
                f"[DEBUG] Skipping '{cef_name}' -> No matching column found in PIMMS report."
            )
            continue

        print(
            f"[DEBUG] Processing '{cef_name}.cef' -> Matched to PIMMS column '{matched_col}'"
        )

        cols_to_select = [col for col in metadata_cols if col in pimms_df.columns] + [
            matched_col
        ]

        sample_pimms_df = pimms_df[cols_to_select][pimms_df[matched_col] > 0]

        target_cef = f"{cef_name}.cef"
        sample_cef_df = all_cef_data[all_cef_data["SourceFile"] == target_cef]

        if sample_cef_df.empty:
            print(f"   -> WARNING: Parsed data for '{target_cef}' is empty.")
            continue

        multi_peak_cef_df = extract_multi_peak_compounds(sample_cef_df)

        if sample_pimms_df.empty or multi_peak_cef_df.empty:
            continue

        mz_matches = match_pimms_to_cef_by_mz(
            sample_pimms_df, multi_peak_cef_df, mass_error_ppm, matched_col
        )
        if mz_matches.empty:
            continue

        ccs_filtered = filter_by_ccs_tolerance(mz_matches, ccs_tolerance)
        if ccs_filtered.empty:
            continue

        rt_diff = abs(ccs_filtered["RT_PIMMS"] - ccs_filtered["RT_CEF"])
        rt_filtered_df = ccs_filtered[rt_diff <= rt_tolerance].copy()
        rt_filtered_df["RT_diff"] = rt_diff[rt_filtered_df.index]
        if rt_filtered_df.empty:
            continue

        anchor_matches_df = rt_filtered_df[
            rt_filtered_df[matched_col].round()
            == rt_filtered_df["Peak_intensity"].round()
        ]

        if anchor_matches_df.empty:
            continue

        print(
            f"   -> SUCCESS: Found {len(anchor_matches_df)} matches in {matched_col}."
        )

        matched_compound_ids = anchor_matches_df["Compound"].unique()

        # 1. Get raw peak data
        full_compound_data = multi_peak_cef_df[
            multi_peak_cef_df["Compound"].isin(matched_compound_ids)
        ].copy()

        # --- NEW: Calculate Kaufman Metrics for these compounds ---
        kaufman_metrics = compute_kaufman_constants(full_compound_data)

        # 2. Prepare Anchor table
        pimms_anchor_cols = [
            "PIMMS_m/z",
            "RT_PIMMS",
            "CCS_PIMMS",
            "DT_PIMMS",
            matched_col,
            "Compound",
            "Match_ID",
            "Classification Type",
        ]

        available_cols = [
            c for c in pimms_anchor_cols if c in anchor_matches_df.columns
        ]

        pimms_anchors = anchor_matches_df[available_cols].drop_duplicates().copy()
        pimms_anchors.rename(columns={matched_col: "PIMMS_Intensity"}, inplace=True)
        pimms_anchors["Sample"] = cef_name

        # 3. Merge PIMMS Anchors with Raw Peak Data
        final_report_df = pd.merge(
            pimms_anchors, full_compound_data, on="Compound", how="left"
        )

        # 4. --- NEW: Merge Kaufman Metrics into the final report ---
        if not kaufman_metrics.empty:
            # Merge on Compound and Sample to align correctly
            final_report_df = pd.merge(
                final_report_df, kaufman_metrics, on=["Compound", "Sample"], how="left"
            )

        all_results_list.append(final_report_df)

    if not all_results_list:
        return pd.DataFrame()
    return pd.concat(all_results_list, ignore_index=True)


# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
if __name__ == "__main__":
    # Define paths (Adjust to match your current setup)
    pimms_report_path = (
        r"PIMMS v1.2\PIMMS output\Paired sample analysis PIMMS report copy.csv"
    )
    cef_folder_path = r"W:\Sampler Research\Final NTA Work\CEF Data"

    print("--- STARTING ANALYSIS ---")

    if not os.path.exists(pimms_report_path) or not os.path.exists(cef_folder_path):
        print("[ERROR] Check paths.")
        exit()

    try:
        print("[INFO] Loading PIMMS report...")
        pimms_df = pd.read_csv(pimms_report_path)
        pimms_df.columns = pimms_df.columns.str.strip()
        print(f"[INFO] Columns cleaned. Found {len(pimms_df)} rows.")

    except Exception as e:
        print(f"[ERROR] Could not read PIMMS report: {e}")
        exit()

    try:
        print("[INFO] Scanning CEF folder...")
        sample_names = get_cef_sample_names(cef_folder_path)

        print("[INFO] Parsing CEF data...")
        all_cef_data = parse_all_cef_files_in_folder(cef_folder_path)
        print(f"[INFO] Parsed {len(all_cef_data)} total peaks from CEF files.")
    except Exception as e:
        print(f"[ERROR] Failed during CEF parsing: {e}")
        exit()

    print("\n[INFO] Running matching pipeline...")
    final_results = run_matching_pipeline(
        pimms_df,
        all_cef_data,
        sample_names,
        mass_error_ppm=10,
        ccs_tolerance=2.0,
        rt_tolerance=1.0,
    )

    if not final_results.empty:
        print(
            f"\n[SUCCESS] Pipeline finished. Generated report with {len(final_results)} rows."
        )
        output_file = "Diagnostic_Analysis_Output_With_Kaufman.csv"
        final_results.to_csv(output_file, index=False)
        print(f"[INFO] Results saved to: {os.path.abspath(output_file)}")
    else:
        print("\n[WARNING] Pipeline finished but no matches were found.")
