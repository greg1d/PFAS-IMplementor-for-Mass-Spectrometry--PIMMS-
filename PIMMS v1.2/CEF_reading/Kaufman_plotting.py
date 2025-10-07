import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.path import Path
from calculating_Kaufman_parameters_file_2 import compute_kaufman_constants
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    get_cef_sample_names,
    run_matching_pipeline,
)


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

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    plot_kaufman_scatter(kaufman_df, boundary_path)

    boundary_df = pd.read_csv(boundary_path)
    contour = Path(boundary_df[["m/C", "MD/C"]].values)
    classified_df = is_point_in_kde_boundary(kaufman_df, contour)

    return classified_df


def main():
    """
    Main function to load data and run the matching process.
    """
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"
    print("Loading PIMMS data...")
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = pimms_df.columns.str.strip()

    print("Parsing all CEF files...")
    all_cef_data = parse_all_cef_files_in_folder(cef_folder)

    sample_names = get_cef_sample_names(cef_folder)

    # 2. Run Pipeline to get a single DataFrame
    final_combined_df = run_matching_pipeline(
        pimms_df,
        all_cef_data,
        sample_names,
        mass_error_ppm=10,
        ccs_tolerance=2.0,
        rt_tolerance=1.0,
    )
    final_combined_df = compute_kaufman_constants(final_combined_df)
    print(final_combined_df)


if __name__ == "__main__":
    main()
