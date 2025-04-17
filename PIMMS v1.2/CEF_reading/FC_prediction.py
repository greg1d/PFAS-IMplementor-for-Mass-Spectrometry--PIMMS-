from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
from Kaufman_plotting import compute_kaufman_constants, show_multi_peak_compound_matches
import numpy as np


def FC_prediction(kaufman_df):
    """
    For each point in kaufman_df, finds the closest valid (m/C, md/C) bin in the Kaufman grid,
    retrieves the F/C value, standard deviation, and Excel-style coordinate.
    If multiple valid bins are found in the search radius, their mean is used.
    """

    # Load mean matrix
    mean_file = r"PIMMS v1.2\CEF_reading\Kaufman_density_plot.csv"
    raw_mean = pd.read_csv(mean_file, header=None)
    m_grid = raw_mean.iloc[0, 1:].astype(float).values  # x-axis
    md_grid = raw_mean.iloc[1:, 0].astype(float).values  # y-axis
    mean_matrix = raw_mean.iloc[1:, 1:].astype(float).values

    # Load stdev matrix
    stdev_file = r"PIMMS v1.2\CEF_reading\Kaufman_density_plot_stdev.csv"
    raw_stdev = pd.read_csv(stdev_file, header=None)
    stdev_matrix = raw_stdev.iloc[1:, 1:].astype(float).values

    # Convert matrix index to Excel coordinate (e.g., B2, C5)

    # Find closest valid average within a radius
    def find_closest_valid_with_excel(m_val, md_val):
        # Compute the distance matrix from the target point to all grid bins
        md_mesh, m_mesh = np.meshgrid(
            md_grid, m_grid, indexing="ij"
        )  # md = rows, m = columns
        distance = np.sqrt((m_mesh - m_val) ** 2 + (md_mesh - md_val) ** 2)

        # Mask invalid entries (NaN or zero)
        mask_valid = (pd.notna(mean_matrix)) & (mean_matrix > 0)
        distance_masked = np.where(mask_valid, distance, np.inf)

        # Find the index of the closest valid point
        min_idx = np.unravel_index(np.argmin(distance_masked), distance_masked.shape)
        i, j = min_idx

        if distance_masked[i, j] == np.inf:
            return np.nan, np.nan, "N/A"

        val = mean_matrix[i, j]
        stdev_val = stdev_matrix[i, j]

        return val, stdev_val

    # Apply function row-wise to DataFrame
    kaufman_df[["Predicted_F_per_C", "Predicted_F_per_C_StDev"]] = kaufman_df.apply(
        lambda row: pd.Series(
            find_closest_valid_with_excel(row["m_over_C"], row["md_over_C"])
        ),
        axis=1,
    )

    return kaufman_df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    kaufman_df = FC_prediction(kaufman_df)
    print(kaufman_df.head())


if __name__ == "__main__":
    main()
