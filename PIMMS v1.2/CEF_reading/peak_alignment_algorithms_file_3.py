import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from calculating_Kaufman_parameters_file_2 import compute_kaufman_constants
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    get_cef_sample_names,
    run_matching_pipeline,
)
# --- Data Extraction, Matching, and Alignment Functions (from previous steps) ---
# For brevity, the full code of these functions is collapsed.
# Ensure they are present in your script as defined in the previous responses.


def align_features(combined_df, ppm_tolerance=10, ccs_tolerance=2.0):
    if combined_df.empty:
        return pd.DataFrame()
    # Include Match_ID in the feature definition
    features_df = (
        combined_df[
            [
                "Sample",
                "Compound",
                "Match_ID",
                "PIMMS_m/z",
                "CCS_PIMMS",
                "PIMMS_Intensity",
            ]
        ]
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


def create_summary_table(final_df):
    """Creates a wide-format summary table, now including Match_ID and Intensity_3."""
    if "AlignmentID" not in final_df.columns or final_df["AlignmentID"].isna().all():
        return pd.DataFrame()
    agg_cols = {
        "Match_ID": "first",  # Take the first Match_ID in the group
        "Peak_mz_1": "mean",
        "PIMMS_CCS": "mean",
        "Peak_mz_2": "mean",
        "Intensity_1": "mean",  # Added average for Peak 1 Intensity
        "Intensity_3": "mean",  # Add Intensity_3 to the summary
        "Kaufman_C": "mean",
        "m_over_C": "mean",
        "mass_defect": "mean",
        "md_over_C": "mean",
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


def plot_kaufman_scatter(kaufman_df):
    """
    Plots an XY scatter plot of md/C (mass defect over C) vs. m/C and overlays the PFAS KDE boundary.

    Parameters:
        kaufman_df (pd.DataFrame): DataFrame with Kaufman constants including 'm_over_C' and 'md_over_C'.
        boundary_csv_path (str): Path to the CSV file containing PFAS KDE boundary with columns 'm/C', 'MD/C'.
    """
    if kaufman_df.empty:
        print("[INFO] No Kaufman data to plot.")
        return
    boundary_csv_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
    plt.figure(figsize=(7, 5))

    # === Plot Kaufman Points ===
    plt.scatter(
        kaufman_df["m_over_C"],
        kaufman_df["md_over_C"],
        color="darkblue",
        edgecolor="black",
        s=50,
        alpha=0.8,
        label="Kaufman Points",
    )

    # === Optional: Overlay KDE Boundary ===
    if boundary_csv_path:
        boundary_df = pd.read_csv(boundary_csv_path)
        if {"m/C", "MD/C"}.issubset(boundary_df.columns):
            plt.plot(
                boundary_df["m/C"],
                boundary_df["MD/C"],
                linestyle="--",
                color="red",
                linewidth=2,
                label="PFAS 90% KDE Boundary",
            )
        else:
            print("[WARNING] Boundary CSV missing required columns: 'm/C', 'MD/C'")

    # === Axes Formatting ===
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.axvline(0, color="gray", linestyle="--", linewidth=1)

    plt.xlabel("m / C", fontsize=12, fontweight="bold")
    plt.ylabel("md / C", fontsize=12, fontweight="bold")
    plt.title("Kaufman Plot: Mass Defect / C vs. m / C", fontsize=14)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    """Main function to run the full workflow."""
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    try:
        # Load Data
        pimms_df = pd.read_csv(pimms_file_path)
        print(pimms_df.head())
        pimms_df.columns = pimms_df.columns.str.strip()
        all_cef_data = parse_all_cef_files_in_folder(cef_folder)

        # Pre-calculate Kaufman Constants (now includes Intensity_3)
        kaufman_df = compute_kaufman_constants(all_cef_data)

        # Run Matching and Alignment Pipeline
        sample_names = get_cef_sample_names(cef_folder)
        combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)

        if combined_df.empty:
            print("\n--- No matches were found, skipping alignment. ---")
            return

        aligned_df = align_features(combined_df)

        # Merge Kaufman data with Aligned Features
        final_long_df = pd.merge(
            aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
        )

        # Create the final summary table
        summary_table = create_summary_table(final_long_df)

        #  Report Final Summary Table
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
