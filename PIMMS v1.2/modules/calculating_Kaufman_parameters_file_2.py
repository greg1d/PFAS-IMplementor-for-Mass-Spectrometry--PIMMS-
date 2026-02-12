import os

import networkx as nx
import numpy as np
import pandas as pd


# --- 1. Kaufman Calculation (Required for pipeline integration) ---
def compute_kaufman_constants(cef_data_df):
    """Computes Kaufman C and extracts intensities for the first 3 peaks."""
    kaufman_data = []
    # Ensure we group by file and compound to isolate specific features
    grouped = cef_data_df.groupby(["SourceFile", "Compound"])

    for (source_file, compound_id), group in grouped:
        if len(group) < 2:
            continue

        # Sort by m/z to ensure we get the M, M+1, M+2 peaks in order
        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)

        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]

        intensity3 = np.nan
        if len(sorted_group) >= 3:
            intensity3 = sorted_group.loc[2, "Peak_intensity"]

        if intensity1 == 0:
            continue

        # Kaufman Calculation: (I2 / I1) * (1 / 0.011145)
        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)

        if kaufman_C == 0:
            continue

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


# --- 2. Feature Alignment ---
def align_features(combined_df, ppm_tolerance=10, ccs_tolerance=2.0):
    if combined_df.empty:
        return pd.DataFrame()

    # MODIFIED: Include Kaufman columns here so they are NOT dropped
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
        # --- NEW COLUMNS PRESERVED ---
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

    # Safe Selection: Only select columns that actually exist in the dataframe
    cols_to_keep = [c for c in feature_cols if c in combined_df.columns]
    features_df = combined_df[cols_to_keep].drop_duplicates().reset_index(drop=True)

    features_df["feature_id"] = list(
        zip(features_df["Sample"], features_df["Compound"])
    )

    # Graph-based alignment logic
    G = nx.Graph()
    G.add_nodes_from(features_df["feature_id"])

    features_df_sorted = features_df.sort_values("PIMMS_m/z").reset_index(drop=True)
    mz_array = features_df_sorted["PIMMS_m/z"].values

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


# --- 3. Summary Creation with Statistics ---
def create_summary_table(final_df):
    if "AlignmentID" not in final_df.columns or final_df["AlignmentID"].isna().all():
        return pd.DataFrame()

    # Define aggregation rules
    agg_cols = {
        "Match_ID": "first",
        "Classification Type": "first",
        "PIMMS_m/z": "mean",
        "PIMMS_CCS": "mean",
        "DT_PIMMS": "mean",
        "RT_PIMMS": "mean",
        # Kaufman Metrics
        "Kaufman_C": "mean",
        "m_over_C": "mean",
        "mass_defect": "mean",
        "md_over_C": "mean",
        "Peak_mz_1": "mean",
        "Intensity_1": "mean",
        "Intensity_2": "mean",
        "Intensity_3": "mean",
    }

    # Filter aggregation dictionary to only include columns present in data
    cols_to_agg = {k: v for k, v in agg_cols.items() if k in final_df.columns}

    # 1. Calculate Means
    summary_metrics = final_df.groupby("AlignmentID").agg(cols_to_agg).reset_index()

    # 2. Calculate Standard Deviations for Kaufman Constants (NEW)
    std_cols = ["Kaufman_C", "m_over_C", "mass_defect"]
    valid_std_cols = [c for c in std_cols if c in final_df.columns]

    if valid_std_cols:
        std_df = final_df.groupby("AlignmentID")[valid_std_cols].std().reset_index()
        # Rename columns to avoid collision (e.g., Kaufman_C_StdDev)
        std_df = std_df.rename(columns={c: f"{c}_StdDev" for c in valid_std_cols})
        summary_metrics = pd.merge(
            summary_metrics, std_df, on="AlignmentID", how="left"
        )

    # 3. Pivot Sample Intensities
    intensity_pivot = final_df.pivot_table(
        index="AlignmentID", columns="Sample", values="PIMMS_Intensity", aggfunc="mean"
    )

    intensity_filled = intensity_pivot.fillna(0)
    summary_metrics["Mean_Intensity"] = intensity_filled.mean(axis=1).values
    summary_metrics["Detection_Count"] = intensity_pivot.count(axis=1).values

    intensity_pivot = intensity_pivot.reset_index().fillna(0)

    # 4. Merge All
    summary_table = pd.merge(
        summary_metrics, intensity_pivot, on="AlignmentID", how="outer"
    )

    return summary_table


# =============================================================================
# MAIN BLOCK TO TEST
# =============================================================================
if __name__ == "__main__":
    # Load the CSV generated by the matching pipeline
    input_file = "Diagnostic_Analysis_Output_With_Kaufman.csv"

    if os.path.exists(input_file):
        print(f"[INFO] Loading {input_file}...")
        df = pd.read_csv(input_file)

        print("[INFO] Aligning features...")
        aligned = align_features(df)

        if not aligned.empty:
            print("[INFO] Creating summary statistics...")
            summary = create_summary_table(aligned)

            output_file = "Final_Summary_With_Kaufman_Stats.csv"
            summary.to_csv(output_file, index=False)
            print(f"[SUCCESS] Summary saved to {output_file}")

            # Print sample of stats
            if "Kaufman_C" in summary.columns and "Kaufman_C_StdDev" in summary.columns:
                print("\nSample Data (First 3 rows):")
                print(summary[["Match_ID", "Kaufman_C", "Kaufman_C_StdDev"]].head(3))
        else:
            print("[ERROR] Alignment produced empty dataframe.")
    else:
        print(
            f"[ERROR] Input file '{input_file}' not found. Run the matching pipeline first."
        )
