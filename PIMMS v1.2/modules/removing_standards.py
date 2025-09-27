import pandas as pd


def remove_standards_library(
    adjusted_df,
    standards_file,
    mass_error_ppm,
    ccs_error_percentage,
    z,
):
    """
    Removes features from the adjusted dataset that match the m/z and CCS
    values found in a standards library.

    Args:
        adjusted_df (pd.DataFrame): The DataFrame to be filtered.
        standards_file (str): Path to the standards library CSV file.
        mass_error_ppm (int): Mass error tolerance in ppm.
        ccs_error_percentage (float): CCS error tolerance as a percentage.
        z (int): Charge state.

    Returns:
        pd.DataFrame: The DataFrame with matched features removed.
    """
    try:
        # --- 1. Load Standards Library (Name column is no longer required) ---
        print("[INFO] Loading standards library to identify features for removal...")
        standards_df = pd.read_csv(standards_file)

        required_columns = {"m/z", "CCS"}
        if not required_columns.issubset(standards_df.columns):
            raise ValueError(
                f"Standards library must contain {required_columns} columns."
            )

        standards_mz = standards_df["m/z"].dropna().to_numpy()
        standards_ccs = standards_df["CCS"].dropna().to_numpy()

        # --- 2. Prepare Experimental Data ---
        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Input DataFrame must contain 'm/z' and 'CCS' columns.")

        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()

        # --- 3. Find Indices of Matched Features ---
        # We will directly collect the indices of rows to be dropped.
        matched_indices = set()
        for i, (exp_mz, exp_ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                mass_tolerance = exp_mz * mass_error_ppm * 1e-6 / z
                ccs_tolerance = std_ccs * ccs_error_percentage / 100

                # Check if the experimental feature falls within the standard's tolerance
                if (
                    std_mz - mass_tolerance <= exp_mz <= std_mz + mass_tolerance
                    and std_ccs - ccs_tolerance <= exp_ccs <= std_ccs + ccs_tolerance
                ):
                    # If a match is found, add its index to the set and stop checking this feature
                    matched_indices.add(adjusted_df.index[i])
                    break

        # --- 4. Remove Matched Rows ---
        # The consolidation step is no longer needed.
        unmatched_df = adjusted_df.drop(index=list(matched_indices), errors="ignore")

        print(
            f"[INFO] Found and removed {len(matched_indices)} features matching the standards library."
        )
        print(f"[INFO] Remaining features: {len(unmatched_df)}")

        return unmatched_df

    except Exception as e:
        print(f"[ERROR] Failed to remove standards: {e}")
        return adjusted_df
