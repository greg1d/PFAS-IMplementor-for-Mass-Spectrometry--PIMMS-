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

    # 7. Plot Kaufman Scatter
    plot_kaufman_scatter(summary_table)
    summary_table.to_csv("aligned_feature_summary.csv", index=False)


if __name__ == "__main__":
    main()
