import pandas as pd
import traceback  # <-- ADD THIS IMPORT AT THE TOP OF THE FILE


def remove_standards_library(
    adjusted_df,
    standards_df,
    mass_error_ppm,
    ccs_error_percentage,
    z,
):
    """
    Removes features from the adjusted dataset that match a pre-standardized
    standards library DataFrame. Assumes both DataFrames have 'm/z' and 'CCS' columns.
    """
    try:
        print("[INFO] Identifying features for removal based on standards library...")

        standards_mz_series = pd.to_numeric(standards_df["m/z"], errors="coerce")
        standards_ccs_series = pd.to_numeric(standards_df["CCS"], errors="coerce")

        standards_mz = standards_mz_series.dropna().to_numpy()
        standards_ccs = standards_ccs_series.dropna().to_numpy()

        if len(standards_mz) == 0 or len(standards_ccs) == 0:
            print(
                "[WARNING] No valid numeric m/z or CCS values found in the standards library after cleaning. Skipping removal."
            )
            return adjusted_df

        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Input DataFrame must contain 'm/z' and 'CCS' columns.")
        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()

        matched_indices = set()
        for i, (exp_mz, exp_ccs) in enumerate(zip(experimental_mz, experimental_ccs)):
            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                mass_tolerance = exp_mz * mass_error_ppm * 1e-6 / z
                ccs_tolerance = std_ccs * ccs_error_percentage / 100
                if (
                    std_mz - mass_tolerance <= exp_mz <= std_mz + mass_tolerance
                    and std_ccs - ccs_tolerance <= exp_ccs <= std_ccs + ccs_tolerance
                ):
                    matched_indices.add(adjusted_df.index[i])
                    break

        unmatched_df = adjusted_df.drop(index=list(matched_indices), errors="ignore")

        print(
            f"[INFO] Found and removed {len(matched_indices)} features matching the standards library."
        )
        print(f"[INFO] Remaining features: {len(unmatched_df)}")

        return unmatched_df

    except Exception as e:
        # --- MODIFIED SECTION ---
        print(f"[ERROR] An unexpected error occurred in remove_standards_library: {e}")
        traceback.print_exc()  # This will print the full, detailed traceback
        return adjusted_df
