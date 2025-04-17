from CEF_matching_algorithm import match_PIMMS_to_CEF, compound_lookup, parse_cef_file
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.path import Path


def extract_multi_peak_compounds(cef_df):
    """Filters for compounds with more than one Peak_mz."""
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    multi_peak_ids = peak_counts[peak_counts > 1].index
    return cef_df[cef_df["Compound"].isin(multi_peak_ids)].copy()


def show_multi_peak_compound_matches(matches, cef_folder):
    """
    For each sample, show compound lookups where matched compounds have >1 Peak_mz.
    Returns a DataFrame of all matched multi-peak compounds with sample info.
    """
    all_multi_peaks = []

    for sample_name, match_df in matches:
        cef_path = os.path.join(cef_folder, f"{sample_name}.cef")
        cef_df = parse_cef_file(cef_path)

        multi_peak_df = extract_multi_peak_compounds(cef_df)

        matched_ids = set(match_df["Compound"])
        multi_peak_ids = set(multi_peak_df["Compound"])
        valid_ids = matched_ids & multi_peak_ids

        filtered_df = multi_peak_df[multi_peak_df["Compound"].isin(valid_ids)].copy()
        filtered_df["SampleName"] = sample_name  # Add sample identity
        all_multi_peaks.append(filtered_df)

        for compound_id in sorted(valid_ids):
            compound_lookup(sample_name, cef_folder, int(compound_id))

    if all_multi_peaks:
        return pd.concat(all_multi_peaks, ignore_index=True)
    else:
        return pd.DataFrame()


def compute_kaufman_constants(multi_peak_df):
    """
    Computes Kaufman C = (I2 / I1) * (1 / 0.011145) and derived metrics:
    - m / C
    - md / C (mass defect / C)

    Returns a DataFrame with all computed metrics per compound per sample.
    """
    kaufman_data = []

    grouped = multi_peak_df.groupby(["SampleName", "Compound"])

    for (sample, compound_id), group in grouped:
        if len(group) < 2:
            continue

        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]
        mz2 = sorted_group.loc[1, "Peak_mz"]

        if intensity1 == 0:
            continue  # Avoid division by zero

        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)
        mass_defect = mz1 - round(mz1)

        kaufman_data.append(
            {
                "Sample": sample,
                "Compound": compound_id,
                "Peak_mz_1": mz1,
                "Intensity_1": intensity1,
                "Peak_mz_2": mz2,
                "Intensity_2": intensity2,
                "Kaufman_C": kaufman_C,
                "m_over_C": mz1 / kaufman_C,
                "mass_defect": mass_defect,
                "md_over_C": mass_defect / kaufman_C,
            }
        )

    return pd.DataFrame(kaufman_data)


def plot_kaufman_scatter(kaufman_df, boundary_csv_path):
    """
    Plots an XY scatter plot of md/C (mass defect over C) vs. m/C and overlays the PFAS KDE boundary.

    Parameters:
        kaufman_df (pd.DataFrame): DataFrame with Kaufman constants including 'm_over_C' and 'md_over_C'.
        boundary_csv_path (str): Path to the CSV file containing PFAS KDE boundary with columns 'm/C', 'MD/C'.
    """
    if kaufman_df.empty:
        print("[INFO] No Kaufman data to plot.")
        return

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


def is_point_in_kde_boundary(kaufman_df, contour_path):
    """
    Adds a column 'inside_PFAS_boundary' to indicate if the Kaufman point lies inside the KDE contour.
    """

    points = kaufman_df[["m_over_C", "md_over_C"]].values
    inside_flags = [contour_path.contains_point(pt) for pt in points]

    kaufman_df["inside_PFAS_boundary"] = inside_flags
    return kaufman_df


def classify_points(matches, cef_folder, boundary_path):
    """
    Filters multi-peak compounds, computes Kaufman constants, plots scatter with contour overlay,
    and classifies points using a KDE boundary.

    Parameters:
        matches (list): Output from match_PIMMS_to_CEF containing (sample, match_df)
        cef_folder (str): Path to folder containing CEF files
        boundary_path (str): Path to CSV file containing the KDE boundary

    Returns:
        pd.DataFrame: Kaufman dataframe with classification results
    """
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    plot_kaufman_scatter(kaufman_df, boundary_path)

    boundary_df = pd.read_csv(boundary_path)
    contour = Path(boundary_df[["m/C", "MD/C"]].values)
    classified_df = is_point_in_kde_boundary(kaufman_df, contour)

    return classified_df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    boundary_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    plot_kaufman_scatter(kaufman_df, boundary_path)


if __name__ == "__main__":
    main()
