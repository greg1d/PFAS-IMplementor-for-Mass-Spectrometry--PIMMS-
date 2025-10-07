import pandas as pd
import xml.etree.ElementTree as ET
import glob
import os
import bisect
# --- Data Extraction and Matching Functions (Unchanged) ---


def get_cef_sample_names(cef_folder):
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    return [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]


def parse_cef_file(cef_file_path):
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
    cef_files = glob.glob(os.path.join(cef_folder_path, "*.cef"))
    if not cef_files:
        raise FileNotFoundError(f"No .cef files found in folder: {cef_folder_path}")
    return pd.concat([parse_cef_file(p) for p in cef_files], ignore_index=True)


def extract_multi_peak_compounds(cef_df):
    if cef_df.empty:
        return pd.DataFrame()
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    return cef_df[cef_df["Compound"].isin(peak_counts[peak_counts > 1].index)].copy()


def run_matching_pipeline(
    pimms_df,
    all_cef_data,
    sample_names,
    mass_error_ppm=10,
    ccs_tolerance=2.0,
    rt_tolerance=1.0,
):
    all_results_list = []
    metadata_cols = ["CCS", "m/z", "RT", "DT", "ID"]
    for sample in sample_names:
        if sample not in pimms_df.columns:
            continue
        sample_pimms_df = pimms_df[metadata_cols + [sample]][pimms_df[sample] > 0]
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
        pimms_anchors = (
            anchor_matches_df[
                ["PIMMS_m/z", "RT_PIMMS", "CCS_PIMMS", sample, "Compound"]
            ]
            .drop_duplicates()
            .copy()
        )
        pimms_anchors.rename(columns={sample: "PIMMS_Intensity"}, inplace=True)
        pimms_anchors["Sample"] = sample
        final_report_df = pd.merge(
            pimms_anchors, full_compound_data, on="Compound", how="left"
        )
        all_results_list.append(final_report_df)
    if not all_results_list:
        return pd.DataFrame()
    return pd.concat(all_results_list, ignore_index=True)


def match_pimms_to_cef_by_mz(pimms_df, cef_df, mass_error_ppm, sample_name):
    cef_mz_array, matched = sorted(cef_df["Peak_mz"].dropna().values), []
    for _, prow in pimms_df.iterrows():
        hits = find_similar_peaks(cef_mz_array, prow["m/z"], mass_error_ppm)
        for cef_mz in hits:
            for _, crow in cef_df[cef_df["Peak_mz"] == cef_mz].iterrows():
                matched.append(
                    {
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
                    }
                )
    return pd.DataFrame(matched)


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
