import numpy as np
import pandas as pd


def smearing_filter(adjusted_df, rt_tolerance=0.5, ppm_tolerance=10, ccs_tolerance=2):
    """
    Filters rows from the adjusted DataFrame to eliminate mass shift rows based on tolerances.

    Args:
        adjusted_df (pd.DataFrame): The adjusted DataFrame containing intensity and metadata columns.
        rt_tolerance (float): Retention time tolerance.
        ppm_tolerance (float): Tolerance for mass shift in ppm.
        ccs_tolerance (float): Tolerance for CCS as a percentage.

    Returns:
        pd.DataFrame: Filtered DataFrame with mass shift rows removed.
    """
    # Identify intensity columns containing ".d"
    intensity_columns = [col for col in adjusted_df.columns if ".d" in col]

    if not intensity_columns:
        raise ValueError("No intensity columns found in the DataFrame.")

    # Sort DataFrame by m/z and reset index
    adjusted_df = adjusted_df.sort_values("m/z").reset_index(drop=True)

    # Create a set of indices to keep
    indices_to_keep = set(adjusted_df.index)

    # Iterate through rows to find and eliminate mass shift rows
    for i in range(len(adjusted_df)):
        if i not in indices_to_keep:
            continue

        mz1 = adjusted_df.loc[i, "m/z"]
        ccs1 = adjusted_df.loc[i, "CCS"]
        retention_time1 = adjusted_df.loc[i, "RT"]

        # Sum intensities for the current row
        intensity1 = adjusted_df.loc[i, intensity_columns].sum()

        # Get potential matches with a higher mass but within tolerances
        potential_matches = adjusted_df[
            (adjusted_df["m/z"] > mz1)  # Higher m/z
            & (
                adjusted_df["m/z"] <= mz1 + ppm_tolerance * mz1 * 1e-6
            )  # Within ppm tolerance
            & (
                abs(adjusted_df["CCS"] - ccs1) / ccs1 * 100 < ccs_tolerance
            )  # CCS difference within tolerance
        ]

        for j in potential_matches.index:
            if j <= i:
                continue

            mz2 = adjusted_df.loc[j, "m/z"]
            ccs2 = adjusted_df.loc[j, "CCS"]
            retention_time2 = adjusted_df.loc[j, "RT"]

            # Sum intensities for the potential match row
            intensity2 = adjusted_df.loc[j, intensity_columns].sum()

            # Calculate differences
            diff_mass_shift = abs(mz2 - mz1)
            ccs_diff = abs(ccs1 - ccs2) / ccs1 * 100
            intensity_diff = intensity1 / intensity2 if intensity2 != 0 else np.inf
            retention_time_diff = abs(retention_time1 - retention_time2)

            # Eliminate row j if conditions are met
            if (
                diff_mass_shift < ppm_tolerance * mz1 * 1e-6
                and ccs_diff < ccs_tolerance
                and intensity_diff > 50
                and retention_time_diff < rt_tolerance
            ):
                indices_to_keep.discard(j)

    # Filter the DataFrame to keep only rows with indices in indices_to_keep
    return adjusted_df.loc[indices_to_keep].reset_index(drop=True)


def main():
    """
    Main function for debugging the smearing_filter function with a sample DataFrame.
    """
    mass_error_ppm = 10
    rt_tolerance = 0.5
    ccs_tolerance = 2.0

    # Create a sample DataFrame for testing
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.666, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 176.79, 175.79, 175.79, 175.79],
            "m/z": [100, 100.00012, 200, 300, 400],
            "148 B2 16632.d.DeMP": [10, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [20, 20, 10, 10, 10],
        }
    )

    # Apply the smearing filter
    filtered_df = smearing_filter(
        adjusted_df, rt_tolerance, mass_error_ppm, ccs_tolerance
    )

    # Print the filtered DataFrame
    print("[INFO] Filtered DataFrame:")
    print(filtered_df)


if __name__ == "__main__":
    main()
