from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
from Kaufman_plotting import compute_kaufman_constants, show_multi_peak_compound_matches
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors


def compute_mCm_alignment(df):
    """
    Computes m/C_m score based on CF2 alignment formula for each row.

    Parameters:
        df (pd.DataFrame): DataFrame containing Peak_mz_1, m_over_C, md_over_C

    Returns:
        pd.DataFrame: Original DataFrame with new column 'm_over_Cm'
    """
    m_cf2 = 49.9968
    md_cf2 = -0.00319

    df = df.copy()
    m = 4.23e-4
    m_over_C = df["m_over_C"]
    md_over_C = df["md_over_C"]

    df["m_over_Cm"] = (m_over_C - m_cf2) * np.cos(m) - (md_over_C - md_cf2) * np.sin(m)

    return df


def compute_MDCm_alignment(df):
    """
    Computes m/C_m score based on CF2 alignment formula for each row.

    Parameters:
        df (pd.DataFrame): DataFrame containing Peak_mz_1, m_over_C, md_over_C

    Returns:
        pd.DataFrame: Original DataFrame with new column 'm_over_Cm'
    """
    m_cf2 = 49.9968
    md_cf2 = -0.00319

    df = df.copy()
    m = 4.23e-4
    m_over_C = df["m_over_C"]
    md_over_C = df["md_over_C"]
    lambda_val = 3000  # Fixed scaling factor

    df["m_over_Cm"] = (
        (m_over_C - m_cf2) * np.cos(m) - (md_over_C - md_cf2) * np.sin(m)
    ) / lambda_val

    df["md_over_Cm"] = (m_over_C - m_cf2) * np.sin(m) + (md_over_C - md_cf2) * np.cos(m)
    return df


def cf2_prioritization(df):
    """
    Calculates the CF₂ prioritization metric (r_CF2) using fixed λ = 3000.

    Parameters:
        df (pd.DataFrame): Must contain 'm_over_Cm' and 'md_over_C'

    Returns:
        pd.DataFrame: Original DataFrame with added 'r_CF2' column
    """
    lambda_val = 3000  # Fixed scaling factor
    df = df.copy()
    df["r_CF2"] = np.sqrt((df["m_over_Cm"] / lambda_val) ** 2 + df["md_over_Cm"] ** 2)
    return df


def plot_kaufman_scatter_colored(kaufman_df):
    """
    Plot Kaufman scatter colored by r_CF2 with exact color range matching reference.
    """
    if kaufman_df.empty:
        print("[INFO] No Kaufman data to plot.")
        return

    # Define custom colormap from red -> green -> blue -> pink
    custom_cmap = mcolors.LinearSegmentedColormap.from_list(
        "custom_kaufman",
        [
            (0.00, "red"),  # 0.01 mapped to red
            (0.33, "lime"),  # green
            (0.66, "blue"),  # blue
            (1.00, "deeppink"),  # 0.05 mapped to pink
        ],
    )

    # Normalize color mapping between r_CF2 values 0.01–0.05
    norm = mcolors.Normalize(vmin=0.01, vmax=0.05)

    # Plot
    plt.figure(figsize=(7, 5))
    scatter = plt.scatter(
        kaufman_df["m_over_Cm"],
        kaufman_df["md_over_Cm"],
        c=kaufman_df["r_CF2"],
        cmap=custom_cmap,
        norm=norm,
        edgecolor="black",
        s=60,
        alpha=0.9,
    )

    # Axes and labels
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.axvline(0, color="gray", linestyle="--", linewidth=1)
    plt.xlabel("m/Cm", fontsize=12, fontweight="bold")
    plt.ylabel("MD/Cm", fontsize=12, fontweight="bold")
    plt.title("Kaufman Plot Colored by $r_{CF_2}$", fontsize=14)

    # Colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label(r"$r_{CF_2}$", fontsize=12, fontweight="bold")
    cbar.set_ticks([0.01, 0.02, 0.03, 0.04, 0.05])

    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    kaufman_df = compute_mCm_alignment(kaufman_df)
    kaufman_df = compute_MDCm_alignment(kaufman_df)
    kaufman_df = cf2_prioritization(kaufman_df)
    print(kaufman_df.head())
    plot_kaufman_scatter_colored(kaufman_df)


if __name__ == "__main__":
    main()
