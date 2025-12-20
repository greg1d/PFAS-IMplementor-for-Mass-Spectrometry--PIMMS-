import networkx as nx
import pandas as pd


def align_features(combined_df, ppm_tolerance=10, ccs_tolerance=2.0):
    if combined_df.empty:
        return pd.DataFrame()
    # MODIFIED: Add 'Classification_Type' to the feature definition
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
    ]
    features_df = combined_df[feature_cols].drop_duplicates().reset_index(drop=True)
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


def create_summary_table(final_df):
    if "AlignmentID" not in final_df.columns or final_df["AlignmentID"].isna().all():
        return pd.DataFrame()
    # MODIFIED: Add 'Classification_Type' to the aggregation rules
    agg_cols = {
        "Match_ID": "first",
        "Classification Type": "first",
        "Peak_mz_1": "mean",
        "Intensity_1": "mean",
        "PIMMS_CCS": "mean",
        "Peak_mz_2": "mean",
        "Intensity_2": "mean",
        "Intensity_3": "mean",
        "Kaufman_C": "mean",
        "m_over_C": "mean",
        "mass_defect": "mean",
        "md_over_C": "mean",
        "DT_PIMMS": "mean",
        "RT_PIMMS": "mean",
    }
    cols_to_agg = {k: v for k, v in agg_cols.items() if k in final_df.columns}
    summary_metrics = final_df.groupby("AlignmentID").agg(cols_to_agg).reset_index()
    intensity_pivot = final_df.pivot_table(
        index="AlignmentID", columns="Sample", values="PIMMS_Intensity", aggfunc="mean"
    ).reset_index()
    summary_table = pd.merge(
        summary_metrics, intensity_pivot, on="AlignmentID", how="outer"
    ).fillna(0)
    return summary_table
