"""
Script to find and visualize contour lines from a 2D density grid CSV.

This script reads a CSV file, interpolates the sparse grid, applies a
Gaussian filter, and uses a DILATED MASK to fill in small gaps while
keeping the plot constrained to the original data's general area.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.ndimage import gaussian_filter, binary_dilation  # <-- Import binary_dilation


def find_and_plot_contours(
    input_path,
    output_csv,
    output_plot,
    levels,
    smoothing_sigma=2.0,
    mask_dilation_iterations=5,
):
    """
    Loads a 2D data grid, smooths it, finds contour boundaries, saves them, and creates a plot.

    Args:
        smoothing_sigma (float): Controls data smoothing. Larger is smoother.
        mask_dilation_iterations (int): Controls gap-filling. Larger fills more space.
    """
    try:
        # 1. Load and clean the data
        print(f"Loading data from '{input_path}'...")
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f"The specified input file was not found: {input_path}"
            )

        density_df = pd.read_csv(input_path, index_col=0)
        valid_columns = [
            col for col in density_df.columns if not str(col).startswith("Unnamed:")
        ]
        density_df = density_df[valid_columns]

        # 2. Create a mask of the original data's valid regions
        original_data_mask = density_df.notna()

        # --- NEW: Dilate the mask to fill in small gaps between valid data points ---
        print(
            f"Dilating data mask with {mask_dilation_iterations} iterations to fill gaps..."
        )
        dilated_mask = binary_dilation(
            original_data_mask, iterations=mask_dilation_iterations
        )
        # --- End of New Code ---

        # 3. Interpolate the sparse data to create a full grid
        print("Interpolating to fill grid...")
        density_df_filled = density_df.interpolate(
            method="linear", axis=1, limit_direction="both"
        )
        density_df_filled = density_df_filled.interpolate(
            method="linear", axis=0, limit_direction="both"
        )

        # 4. Prepare the data grid
        print("Preparing data grid...")
        Z = density_df_filled.values
        x_coords = density_df_filled.columns.astype(float)
        y_coords = density_df_filled.index.astype(float)
        X, Y = np.meshgrid(x_coords, y_coords)

        # 5. Apply Gaussian smoothing
        print(f"Applying Gaussian smoothing with sigma={smoothing_sigma}...")
        Z_smoothed = gaussian_filter(Z, sigma=smoothing_sigma)

        # 6. Apply the DILATED mask to the smoothed data
        Z_smoothed[~dilated_mask] = np.nan
        print("Masking smoothed data to dilated original bounds.")

        # 7. Find and extract contours using the MASKED and SMOOTHED data
        print(f"Calculating contours for levels: {levels}...")
        fig_temp, ax_temp = plt.subplots()
        contours = ax_temp.contour(X, Y, Z_smoothed, levels=levels)
        plt.close(fig_temp)

        all_boundary_points = []
        for i, level in enumerate(contours.levels):
            for seg_id, segment in enumerate(contours.allsegs[i]):
                for point in segment:
                    all_boundary_points.append(
                        {
                            "level": level,
                            "segment_id": f"{level}_{seg_id}",
                            "m/C": point[0],
                            "MD/C": point[1],
                        }
                    )

        if all_boundary_points:
            pd.DataFrame(all_boundary_points).to_csv(output_csv, index=False)
            print(f"\nSuccessfully saved SMOOTHED boundary data to '{output_csv}'")
        else:
            print("\nWarning: No contour boundaries could be extracted.")

        # 8. Generate a confirmation plot
        print("\nGenerating visualization...")
        plt.figure(figsize=(10, 8))
        plt.pcolormesh(X, Y, Z_smoothed, cmap="viridis", alpha=0.7, shading="gouraud")
        plt.colorbar(label="Smoothed & Masked Density Value")
        contour_lines = plt.contour(
            X, Y, Z_smoothed, levels=levels, colors="black", linewidths=1.5
        )
        plt.clabel(contour_lines, inline=True, fontsize=10, fmt="%1.2f")
        plt.xlabel("m/C", fontsize=12)
        plt.ylabel("MD/C", fontsize=12)
        plt.title("Kaufman Density Plot with Smoothed & Bounded Contours", fontsize=14)
        plt.xlim(x_coords.min(), x_coords.max())
        plt.ylim(y_coords.min(), y_coords.max())
        plt.savefig(output_plot)
        print(f"Plot saved to '{output_plot}'")
        plt.show()

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    # --- USER CONFIGURATION ---
    INPUT_CSV_PATH = r"PIMMS v1.2\CEF_reading\Kaufman_density_plot.csv"
    OUTPUT_BOUNDARIES_CSV_PATH = (
        r"PIMMS v1.2\CEF_reading\kaufman_contour_boundaries_SMOOTH.csv"
    )
    OUTPUT_PLOT_PATH = "kaufman_density_contours_SMOOTH.png"
    CONTOUR_LEVELS = [
        0.8,
        0.9,
        1,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
        1.6,
        1.7,
        1.8,
        1.9,
        2,
        2.1,
        2.2,
    ]
    SMOOTHING_SIGMA = 2.0

    # NEW: Controls how much to fill in empty gaps.
    # Higher values connect regions that are further apart. Try values between 2 and 10.
    MASK_DILATION_ITERATIONS = 4

    # --- SCRIPT EXECUTION ---
    find_and_plot_contours(
        input_path=INPUT_CSV_PATH,
        output_csv=OUTPUT_BOUNDARIES_CSV_PATH,
        output_plot=OUTPUT_PLOT_PATH,
        levels=CONTOUR_LEVELS,
        smoothing_sigma=SMOOTHING_SIGMA,
        mask_dilation_iterations=MASK_DILATION_ITERATIONS,
    )
