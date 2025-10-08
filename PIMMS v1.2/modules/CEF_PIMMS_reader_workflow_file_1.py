import pandas as pd
import xml.etree.ElementTree as ET
import glob
import os
import bisect
import numpy as np

# --- Data Extraction and Calculation Functions ---


def get_cef_sample_names(cef_folder):
    """Returns a list of sample names from .cef files."""
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    return [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]


def parse_cef_file(cef_file_path):
    """Parses a .cef XML file."""
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


def parse_all_cef_files_in_folder(cef_folder_path):
    """Parses all .cef files in a given folder."""
    cef_files = glob.glob(os.path.join(cef_folder_path, "*.cef"))
    if not cef_files:
        raise FileNotFoundError(f"No .cef files found in folder: {cef_folder_path}")
    return pd.concat([parse_cef_file(p) for p in cef_files], ignore_index=True)


def compute_kaufman_constants(cef_data_df):
    """Computes Kaufman C and extracts intensities for the first 3 peaks."""
    kaufman_data = []
    grouped = cef_data_df.groupby(["SourceFile", "Compound"])
    for (source_file, compound_id), group in grouped:
        if len(group) < 2:
            continue
        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1, intensity2, mz1 = (
            sorted_group.loc[0, "Peak_intensity"],
            sorted_group.loc[1, "Peak_intensity"],
            sorted_group.loc[0, "Peak_mz"],
        )
        intensity3 = np.nan
        if len(sorted_group) >= 3:
            intensity3 = sorted_group.loc[2, "Peak_intensity"]
        if intensity1 == 0:
            continue
        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)
        if kaufman_C == 0:
            continue
        mass_defect, sample_name = (
            mz1 - round(mz1),
            os.path.splitext(source_file)[0].strip(),
        )
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
    """
    MODIFIED: Now passes 'Match_ID' and 'Classification_Type' from PIMMS data.
    """
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
                    "Peak_intensity": crow["Peak_intensity"],
                    sample_name: prow[sample_name],
                    "Compound": crow["Compound"],
                    "Match_ID": prow.get("Match", "N/A"),  # Safely get 'Match'
                    "Classification_Type": prow.get(
                        "Classification_Type", "N/A"
                    ),  # Safely get 'Classification_Type'
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
    all_results_list = []
    # MODIFIED: Add "Classification_Type" to the list of columns to keep
    metadata_cols = ["CCS", "m/z", "RT", "DT", "ID", "Match", "Classification_Type"]
    for sample in sample_names:
        if sample not in pimms_df.columns:
            continue
        cols_to_select = [col for col in metadata_cols if col in pimms_df.columns] + [
            sample
        ]
        sample_pimms_df = pimms_df[cols_to_select][pimms_df[sample] > 0]
        sample_cef_df = all_cef_data[all_cef_data["SourceFile"] == f"{sample}.cef"]
        multi_peak_cef_df = extract_multi_peak_compounds(sample_cef_df)
        if sample_pimms_df.empty or multi_peak_cef_df.empty:
            continue
        mz_matches = match_pimms_to_cef_by_mz(
            sample_pimms_df, multi_peak_cef_df, mass_error_ppm, sample
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
            rt_filtered_df[sample].round() == rt_filtered_df["Peak_intensity"].round()
        ]
        if anchor_matches_df.empty:
            continue
        matched_compound_ids = anchor_matches_df["Compound"].unique()
        full_compound_data = multi_peak_cef_df[
            multi_peak_cef_df["Compound"].isin(matched_compound_ids)
        ].copy()
        # MODIFIED: Include 'Classification_Type' when defining the anchor features
        pimms_anchor_cols = [
            "PIMMS_m/z",
            "RT_PIMMS",
            "CCS_PIMMS",
            sample,
            "Compound",
            "Match_ID",
            "Classification_Type",
        ]
        pimms_anchors = anchor_matches_df[pimms_anchor_cols].drop_duplicates().copy()
        pimms_anchors.rename(columns={sample: "PIMMS_Intensity"}, inplace=True)
        pimms_anchors["Sample"] = sample
        final_report_df = pd.merge(
            pimms_anchors, full_compound_data, on="Compound", how="left"
        )
        all_results_list.append(final_report_df)
    if not all_results_list:
        return pd.DataFrame()
    return pd.concat(all_results_list, ignore_index=True)
