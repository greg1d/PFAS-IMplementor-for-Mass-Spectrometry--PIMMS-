import pandas as pd
import traceback


def remove_standards_library(
    adjusted_df,
    standards_df,
    mass_error_ppm,
    ccs_error_percentage,
    z,
):
    """
    Removes features from the adjusted dataset that match a pre-standardized
    standards library DataFrame, including M-1 artifacts. Assumes both
    DataFrames have 'm/z' and 'CCS' columns.
    """
    try:
        print(
            "[INFO] Identifying features for removal based on standards library (including M-1 artifacts)..."
        )

        # --- Force columns to be numeric to prevent type errors ---
        standards_mz_series = pd.to_numeric(standards_df["m/z"], errors="coerce")
        standards_ccs_series = pd.to_numeric(standards_df["CCS"], errors="coerce")

        standards_mz = standards_mz_series.dropna().to_numpy()
        standards_ccs = standards_ccs_series.dropna().to_numpy()

        if len(standards_mz) == 0 or len(standards_ccs) == 0:
            print(
                "[WARNING] No valid numeric m/z or CCS values found in the standards library after cleaning. Skipping removal."
            )
            return adjusted_df

        # --- Prepare Experimental Data (unchanged) ---
        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Input DataFrame must contain 'm/z' and 'CCS' columns.")
        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()

        # --- Find Indices of Matched Features ---
        matched_indices = set()
        for i, (exp_mz, exp_ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                mass_tolerance = exp_mz * mass_error_ppm * 1e-6 / z
                ccs_tolerance = std_ccs * ccs_error_percentage / 100

                # --- MODIFIED LOGIC ---
                # First, check if the CCS matches, as this is required for both conditions.
                ccs_match = (
                    std_ccs - ccs_tolerance <= exp_ccs <= std_ccs + ccs_tolerance
                )

                if ccs_match:
                    # Condition A: Check for a direct m/z match
                    direct_mz_match = (
                        std_mz - mass_tolerance <= exp_mz <= std_mz + mass_tolerance
                    )

                    # Condition B: Check for the M-1 artifact m/z match
                    std_mz_minus_one = std_mz - 1.0
                    m_minus_one_mz_match = (
                        std_mz_minus_one - mass_tolerance
                        <= exp_mz
                        <= std_mz_minus_one + mass_tolerance
                    )

                    # If either the direct mass or the M-1 artifact mass matches, remove the feature.
                    if direct_mz_match or m_minus_one_mz_match:
                        matched_indices.add(adjusted_df.index[i])
                        # A match was found, no need to check against other standards, so break.
                        break

        # --- Remove Matched Rows (unchanged) ---
        unmatched_df = adjusted_df.drop(index=list(matched_indices), errors="ignore")

        print(
            f"[INFO] Found and removed {len(matched_indices)} features matching the standards library or their M-1 artifacts."
        )
        print(f"[INFO] Remaining features: {len(unmatched_df)}")

        return unmatched_df

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in remove_standards_library: {e}")
        traceback.print_exc()
        return adjusted_df
