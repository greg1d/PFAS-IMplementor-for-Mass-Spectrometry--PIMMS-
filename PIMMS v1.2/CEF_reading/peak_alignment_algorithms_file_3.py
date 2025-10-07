import pandas as pd
import xml.etree.ElementTree as ET
import glob
import os
import bisect
import networkx as nx

# --- Data Extraction, Matching, and Alignment Functions (from previous steps) ---
# For brevity, the full code of these functions is collapsed.
# Ensure they are present in your script as defined in the previous responses.


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


def align_features(combined_df, ppm_tolerance=10, ccs_tolerance=2.0):
    if combined_df.empty:
        return pd.DataFrame()
    features_df = (
        combined_df[["Sample", "Compound", "PIMMS_m/z", "CCS_PIMMS", "PIMMS_Intensity"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    features_df["feature_id"] = list(
        zip(features_df["Sample"], features_df["Compound"])
    )
    G = nx.Graph(list(features_df["feature_id"]))
    features_df_sorted = features_df.sort_values("PIMMS_m/z").reset_index(drop=True)
    mz_array = features_df_sorted["PIMMS_m/z"]
    for _, base in features_df_sorted.iterrows():
        err = base["PIMMS_m/z"] * ppm_tolerance * 1e-6
        idxs = mz_array.searchsorted([base["PIMMS_m/z"] - err, base["PIMMS_m/z"] + err])
        for _, target in features_df_sorted.iloc[idxs[0] : idxs[1]].iterrows():
            if (
                base["Sample"] != target["Sample"]
                and (abs(base["CCS_PIMMS"] - target["CCS_PIMMS"]) / base["CCS_PIMMS"])
                * 100
                <= ccs_tolerance
            ):
                G.add_edge(base["feature_id"], target["feature_id"])
    id_map = {
        fid: i + 1 for i, grp in enumerate(nx.connected_components(G)) for fid in grp
    }
    features_df["AlignmentID"] = features_df["feature_id"].map(id_map)
    features_df.rename(columns={"CCS_PIMMS": "PIMMS_CCS"}, inplace=True)
    return features_df.drop(columns=["feature_id"])


def compute_kaufman_constants(cef_data_df):
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
        if intensity1 == 0:
            continue
        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)
        if kaufman_C == 0:
            continue
        mass_defect = mz1 - round(mz1)
        sample_name = os.path.splitext(source_file)[0].strip()
        kaufman_data.append(
            {
                "Sample": sample_name,
                "Compound": compound_id,
                "Kaufman_C": kaufman_C,
                "m_over_C": mz1 / kaufman_C,
                "mass_defect": mass_defect,
                "md_over_C": mass_defect / kaufman_C,
                "Peak_mz_1": mz1,
                "Peak_mz_2": sorted_group.loc[1, "Peak_mz"],
            }
        )
    return pd.DataFrame(kaufman_data)


# --- NEW Summary Table Function ---


def create_summary_table(final_df):
    """
    Pivots the long-format aligned data into a wide-format summary table.
    Each row is a unique AlignmentID, and columns contain aggregated metrics
    and per-sample intensities.
    """
    if "AlignmentID" not in final_df.columns or final_df["AlignmentID"].isna().all():
        print("[INFO] No valid AlignmentIDs found to create a summary table.")
        return pd.DataFrame()

    # 1. Define the columns to average for each aligned feature
    agg_cols = {
        "Peak_mz_1": "mean",
        "PIMMS_CCS": "mean",  # Use the PIMMS_CCS as the representative CCS
        "Peak_mz_2": "mean",
        "Kaufman_C": "mean",
        "m_over_C": "mean",
        "mass_defect": "mean",
        "md_over_C": "mean",
    }

    # Filter for columns that actually exist in the DataFrame to avoid KeyErrors
    cols_to_agg = {k: v for k, v in agg_cols.items() if k in final_df.columns}

    summary_metrics = final_df.groupby("AlignmentID").agg(cols_to_agg).reset_index()

    # 2. Pivot the table to get PIMMS_Intensity for each sample as a new column
    intensity_pivot = final_df.pivot_table(
        index="AlignmentID",
        columns="Sample",
        values="PIMMS_Intensity",
        aggfunc="mean",  # Use mean to handle cases where one sample has multiple features in an alignment group
    ).reset_index()

    # 3. Merge the averaged metrics with the pivoted intensities
    summary_table = pd.merge(
        summary_metrics, intensity_pivot, on="AlignmentID", how="outer"
    )

    # Fill any missing intensity values with 0 (meaning not detected)
    summary_table = summary_table.fillna(0)

    return summary_table


def main():
    """
    Main function to load data, run the full pipeline, and generate a summary table.
    """
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    try:
        # 1. Load Data
        pimms_df = pd.read_csv(pimms_file_path)
        pimms_df.columns = pimms_df.columns.str.strip()
        all_cef_data = parse_all_cef_files_in_folder(cef_folder)

        # 2. Pre-calculate Kaufman Constants
        kaufman_df = compute_kaufman_constants(all_cef_data)

        # 3. Run Matching and Alignment Pipeline
        sample_names = get_cef_sample_names(cef_folder)
        combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)
        if combined_df.empty:
            print("\n--- No matches were found, skipping alignment. ---")
            return

        aligned_df = align_features(combined_df)

        # 4. Merge Kaufman data with Aligned Features
        final_long_df = pd.merge(
            aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
        )

        # 5. NEW: Create the final summary table
        summary_table = create_summary_table(final_long_df)

        # 6. Report Final Summary Table
        print("\n\n--- Final Feature Summary Table ---")
        if summary_table.empty:
            print("Could not generate a summary table.")
        else:
            print(
                f"Successfully generated a summary table with {len(summary_table)} aligned features."
            )
            print(summary_table)

    except (FileNotFoundError, TypeError) as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
