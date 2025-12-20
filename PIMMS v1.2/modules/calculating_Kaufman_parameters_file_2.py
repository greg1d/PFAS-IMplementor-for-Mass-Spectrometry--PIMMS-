import os

import networkx as nx
import numpy as np
import pandas as pd


def align_features(combined_df, ppm_tolerance=10, ccs_tolerance=2.0):
    if combined_df.empty:
        return pd.DataFrame()

    # --- MODIFIED: Added Kaufman metrics to feature_cols to preserve them ---
    feature_cols = [
        "Sample",
        "Compound",
        "Match_ID",
        "Classification Type",
        "PIMMS_m/z",
        "CCS_PIMMS",
        "PIMMS_Intensity",
        "DT_PIMMS",
        "RT_PIMMS",
        # Kaufman & Peak Data
        "Kaufman_C",
        "m_over_C",
        "mass_defect",
        "md_over_C",
        "Peak_mz_1",
        "Intensity_1",
        "Peak_mz_2",
        "Intensity_2",
        "Intensity_3",
    ]

    # Filter to only columns that actually exist in the input DF
    existing_cols = [c for c in feature_cols if c in combined_df.columns]
    features_df = combined_df[existing_cols].drop_duplicates().reset_index(drop=True)

    features_df["feature_id"] = list(
        zip(features_df["Sample"], features_df["Compound"])
    )

    G = nx.Graph()
    G.add_nodes_from(features_df["feature_id"])

    features_df_sorted = features_df.sort_values("PIMMS_m/z").reset_index(drop=True)
    mz_array = features_df_sorted["PIMMS_m/z"].values

    # Vectorized search for graph edges
    for i, base in features_df_sorted.iterrows():
        err = base["PIMMS_m/z"] * ppm_tolerance * 1e-6
        min_mz, max_mz = base["PIMMS_m/z"] - err, base["PIMMS_m/z"] + err

        start_idx = mz_array.searchsorted(min_mz)
        end_idx = mz_array.searchsorted(max_mz, side="right")

        candidates = features_df_sorted.iloc[start_idx:end_idx]

        for _, target in candidates.iterrows():
            if base["feature_id"] == target["feature_id"]:
                continue
            if base["Sample"] == target["Sample"]:
                continue

            ccs_diff = (
                abs(base["CCS_PIMMS"] - target["CCS_PIMMS"]) / base["CCS_PIMMS"] * 100
            )
            if ccs_diff <= ccs_tolerance:
                G.add_edge(base["feature_id"], target["feature_id"])

    id_map = {
        fid: i + 1 for i, grp in enumerate(nx.connected_components(G)) for fid in grp
    }

    features_df["AlignmentID"] = features_df["feature_id"].map(id_map)
    features_df.rename(columns={"CCS_PIMMS": "PIMMS_CCS"}, inplace=True)

    return features_df.drop(columns=["feature_id"])


def create_summary_table(final_df):
    if "AlignmentID" not in final_df.columns or final_df["AlignmentID"].isna().all():
        return pd.DataFrame()

    # --- Aggregation Rules ---
    agg_cols = {
        "Match_ID": "first",
        "Classification Type": "first",
        "PIMMS_m/z": "mean",
        "PIMMS_CCS": "mean",
        "DT_PIMMS": "mean",
        "RT_PIMMS": "mean",
        # Kaufman Averages
        "Kaufman_C": "mean",
        "m_over_C": "mean",
        "mass_defect": "mean",
        "md_over_C": "mean",
        "Peak_mz_1": "mean",
        "Intensity_1": "mean",
        "Intensity_2": "mean",
        "Intensity_3": "mean",
    }
    cols_to_agg = {k: v for k, v in agg_cols.items() if k in final_df.columns}

    # 1. Calculate Means
    summary_metrics = final_df.groupby("AlignmentID").agg(cols_to_agg).reset_index()

    # 2. Calculate Standard Deviation for Kaufman C (to track variation)
    if "Kaufman_C" in final_df.columns:
        kaufman_std = final_df.groupby("AlignmentID")["Kaufman_C"].std().reset_index()
        kaufman_std.rename(columns={"Kaufman_C": "Kaufman_C_StdDev"}, inplace=True)
        summary_metrics = pd.merge(
            summary_metrics, kaufman_std, on="AlignmentID", how="left"
        )

    # 3. Pivot for Sample Intensities
    intensity_pivot = final_df.pivot_table(
        index="AlignmentID", columns="Sample", values="PIMMS_Intensity", aggfunc="mean"
    )

    # Intensity Stats (All Samples, treating NaN as 0)
    intensity_filled = intensity_pivot.fillna(0)
    summary_metrics["Mean_Intensity_All"] = intensity_filled.mean(axis=1).values
    summary_metrics["StdDev_Intensity_All"] = intensity_filled.std(axis=1).values
    summary_metrics["Detection_Count"] = intensity_pivot.count(axis=1).values

    # Reset pivot index for merge
    intensity_pivot = intensity_pivot.reset_index().fillna(0)

    # 4. Merge Everything
    summary_table = pd.merge(
        summary_metrics, intensity_pivot, on="AlignmentID", how="outer"
    )

    return summary_table


# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
if __name__ == "__main__":
    # Use the file produced in the previous step
    input_csv = "Diagnostic_Analysis_Output_With_Kaufman.csv"

    if not os.path.exists(input_csv):
        print(
            f"[ERROR] Could not find {input_csv}. Please run the previous analysis script first."
        )
        exit()

    print(f"[INFO] Loading {input_csv}...")
    combined_data = pd.read_csv(input_csv)

    # Quick check if Kaufman columns exist
    if "Kaufman_C" in combined_data.columns:
        print("[INFO] Kaufman data detected. Proceeding with alignment.")
    else:
        print("[WARNING] 'Kaufman_C' column missing. Averages will not be calculated.")

    print("[INFO] Aligning features across samples...")
    aligned_df = align_features(combined_data)

    if aligned_df.empty:
        print("[WARNING] No features aligned.")
        exit()

    print("[INFO] Creating summary table...")
    summary = create_summary_table(aligned_df)

    # --- DIAGNOSTIC: Check variations in Kaufman C ---
    multi_sample_features = summary[summary["Detection_Count"] > 1]

    if not multi_sample_features.empty and "Kaufman_C" in summary.columns:
        # Pick the feature with the highest detection count to show variation
        example = multi_sample_features.sort_values(
            "Detection_Count", ascending=False
        ).iloc[0]
        aid = example["AlignmentID"]

        print("\n" + "=" * 60)
        print(f"KAUFMAN VARIATION REPORT FOR ALIGNMENT ID: {aid}")
        print("=" * 60)
        print(f"Match: {example.get('Match_ID', 'N/A')}")

        # Get raw values from aligned df
        raw_rows = aligned_df[aligned_df["AlignmentID"] == aid]

        print(f"\nRaw Kaufman C values across {len(raw_rows)} samples:")
        k_values = []
        for _, row in raw_rows.iterrows():
            k_val = row.get("Kaufman_C", np.nan)
            k_values.append(k_val)
            print(f"  - Sample: {row['Sample']:<30} Kaufman C: {k_val:.4f}")

        print("-" * 30)
        print("CALCULATED AGGREGATES:")
        print(f"  Mean Kaufman C:       {example['Kaufman_C']:.4f}")
        print(f"  StdDev Kaufman C:     {example.get('Kaufman_C_StdDev', 0):.4f}")
        print("-" * 30)

        # Manual Verify
        import statistics

        valid_k = [x for x in k_values if pd.notna(x)]
        if len(valid_k) > 1:
            manual_mean = statistics.mean(valid_k)
            if abs(manual_mean - example["Kaufman_C"]) < 0.0001:
                print("[SUCCESS] Mean calculation verified.")
            else:
                print(
                    f"[WARNING] Mean mismatch! Manual: {manual_mean:.4f} vs Auto: {example['Kaufman_C']:.4f}"
                )

    # Save output
    output_file = "Final_Statistical_Summary.csv"
    summary.to_csv(output_file, index=False)
    print(f"\n[INFO] Full summary saved to: {os.path.abspath(output_file)}")
