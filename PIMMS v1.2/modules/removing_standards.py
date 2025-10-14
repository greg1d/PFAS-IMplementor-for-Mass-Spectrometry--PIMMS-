import pandas as pd


def remove_standards_library(
    adjusted_df,
    standards_df,
    mass_error_ppm,
    ccs_error_percentage,
):
    """
    Removes features from the adjusted dataset that match a pre-standardized
    standards library DataFrame, including M-1 artifacts.
    Only removes features with Classification Type 'unmatched' or 'tentative'.
    Assumes both DataFrames have 'm/z' and 'CCS' columns.
    """
    if adjusted_df.empty or standards_df.empty:
        print("[INFO] Input DataFrame is empty. Skipping standards library removal.")
        return adjusted_df
    try:
        print(
            "[INFO] Identifying features for removal based on standards library (including M-1 artifacts)..."
        )

        # --- Force columns to be numeric to prevent type errors ---
        standards_mz = (
            pd.to_numeric(standards_df["m/z"], errors="coerce").dropna().to_numpy()
        )
        standards_ccs = (
            pd.to_numeric(standards_df["CCS"], errors="coerce").dropna().to_numpy()
        )

        if len(standards_mz) == 0 or len(standards_ccs) == 0:
            print(
                "[WARNING] No valid numeric m/z or CCS values found in the standards library. Skipping removal."
            )
            return adjusted_df

        # --- Prepare Experimental Data ---
        if "m/z" not in adjusted_df.columns or "CCS" not in adjusted_df.columns:
            raise ValueError("Input DataFrame must contain 'm/z' and 'CCS' columns.")
        experimental_mz = adjusted_df["m/z"].to_numpy()
        experimental_ccs = adjusted_df["CCS"].to_numpy()
        classification_types = adjusted_df.get(
            "Classification Type", pd.Series(["unmatched"] * len(adjusted_df))
        )

        # --- Find Indices of Matched Features ---
        matched_indices = set()
        for i, (exp_mz, exp_ccs, cls_type) in enumerate(
            zip(experimental_mz, experimental_ccs, classification_types)
        ):
            if cls_type not in ["unmatched", "tentative"]:
                continue  # Only consider 'unmatched' or 'tentative'

            for std_mz, std_ccs in zip(standards_mz, standards_ccs):
                mass_tolerance = std_mz * mass_error_ppm * 1e-6
                ccs_tolerance = std_ccs * ccs_error_percentage / 100

                # Check CCS match
                ccs_match = (
                    std_ccs - ccs_tolerance <= exp_ccs <= std_ccs + ccs_tolerance
                )
                if not ccs_match:
                    continue

                # Check direct m/z match or M-1 artifact
                direct_mz_match = (
                    std_mz - mass_tolerance <= exp_mz <= std_mz + mass_tolerance
                )
                m_minus_one_mz_match = (
                    std_mz - 1.0 - mass_tolerance
                    <= exp_mz
                    <= std_mz - 1.0 + mass_tolerance
                )

                if direct_mz_match or m_minus_one_mz_match:
                    matched_indices.add(adjusted_df.index[i])
                    break  # Stop checking other standards once matched

        # --- Remove Matched Rows ---
        filtered_df = adjusted_df.drop(index=list(matched_indices), errors="ignore")

        print(
            f"[INFO] Found and removed {len(matched_indices)} features with 'unmatched' or 'tentative' Classification Type matching the standards library or M-1 artifacts."
        )
        print(f"[INFO] Remaining features: {len(filtered_df)}")

        return filtered_df

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in remove_standards_library: {e}")
        import traceback

        traceback.print_exc()
        return adjusted_df
