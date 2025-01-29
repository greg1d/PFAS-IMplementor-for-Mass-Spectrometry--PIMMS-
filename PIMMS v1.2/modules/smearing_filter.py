import pandas as pd


def smearing_filter(adjusted_df, rt_tolerance=0.5, ccs_tolerance=2):
    """
    Filters rows from the adjusted DataFrame to eliminate mass shift rows based on tolerances.
    If a peak is significantly stronger in a `.d` column, the weaker peak is set to 0 in that column.

    Args:
        adjusted_df (pd.DataFrame): The adjusted DataFrame containing intensity and metadata columns.
        rt_tolerance (float): Retention time tolerance.
        ccs_tolerance (float): Tolerance for CCS as a percentage.

    Returns:
        pd.DataFrame: Filtered DataFrame where weaker intensities are zeroed out in relevant `.d` columns.
    """
    # Identify intensity columns containing ".d"
    intensity_columns = [col for col in adjusted_df.columns if ".d" in col]
    if not intensity_columns:
        raise ValueError("No intensity columns found in the DataFrame.")

    print(f"\n[DEBUG] Identified intensity columns: {intensity_columns}")

    # Sort DataFrame by Experimental m/z and reset index
    adjusted_df = adjusted_df.sort_values("m/z").reset_index(drop=True)
    print(f"\n[DEBUG] Sorted DataFrame by m/z:\n{adjusted_df[['m/z', 'RT', 'CCS']]}")

    # Iterate through rows to find and eliminate weaker intensity values
    for i in range(len(adjusted_df)):
        mz1 = adjusted_df.loc[i, "m/z"]
        ccs1 = adjusted_df.loc[i, "CCS"]
        retention_time1 = adjusted_df.loc[i, "RT"]

        print(
            f"\n[DEBUG] Processing row {i}: m/z={mz1}, CCS={ccs1}, RT={retention_time1}"
        )

        # Get potential matches with a **lower mass (-2 Da cutoff)** but within tolerances
        potential_matches = adjusted_df[
            (adjusted_df["m/z"] >= mz1 - 2)  # Within -2 Da cutoff
            & (adjusted_df["m/z"] < mz1)  # Ensure it's a lower mass shift
            & (
                abs(adjusted_df["CCS"] - ccs1) / ccs1 * 100 < ccs_tolerance
            )  # CCS difference within tolerance
            & (
                abs(adjusted_df["RT"] - retention_time1) <= rt_tolerance
            )  # RT difference within tolerance
        ]

        if potential_matches.empty:
            print(f"[DEBUG] No potential matches found for row {i}.")
            continue

        print(
            f"[DEBUG] Found {len(potential_matches)} potential match(es) for row {i}."
        )

        for j in potential_matches.index:
            if j >= i:  # Ensure we compare with the lower mass peak
                continue

            mz2 = adjusted_df.loc[j, "m/z"]
            ccs2 = adjusted_df.loc[j, "CCS"]
            retention_time2 = adjusted_df.loc[j, "RT"]

            print(
                f"[DEBUG] Comparing row {i} (m/z={mz1}) with row {j} (m/z={mz2}):"
                f"\n      CCS Diff: {abs(ccs1 - ccs2) / ccs1 * 100:.2f}%"
                f"\n      RT Diff: {abs(retention_time1 - retention_time2):.3f}"
            )

            # Compare each intensity column separately
            for col in intensity_columns:
                int1 = adjusted_df.at[i, col]
                int2 = adjusted_df.at[j, col]

                print(f"   [DEBUG] Intensity in {col}: Row {i}={int1}, Row {j}={int2}")

                # If the intensity of peak j (lower mass) is much stronger, zero out peak i in that column
                if int2 > 50 * int1:
                    print(
                        f"   [DEBUG] Row {i} in {col} will be zeroed out (Lower mass dominates)."
                    )
                    adjusted_df.at[i, col] = 0  # Zero out weak peak

    print("\n[DEBUG] Final processed DataFrame:")
    print(adjusted_df)
    return adjusted_df


def main():
    """
    Main function for debugging the smearing_filter function with a sample DataFrame.
    """
    rt_tolerance = 0.5
    ccs_tolerance = 2.0

    # Create a sample DataFrame for testing
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5, 6],
            "RT": [3.4, 3.4, 3.665, 3.666, 3.664, 3.7],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319, 23.500],
            "CCS": [175.79, 176.79, 175.79, 175.79, 175.79, 175.79],
            "m/z": [98, 100, 198, 200, 298, 300],  # Mass shift scenario (-2 Da)
            "148 B2 16632.d.DeMP": [
                10000,
                10,
                10000,
                10,
                10000,
                10,
            ],  # High intensity dominates
            "149 B2 16631.d.DeMP": [10, 10, 10, 10, 10, 10],  # Equal intensity retained
        }
    )

    print("[INFO] Original DataFrame:")
    print(adjusted_df)

    # Apply the smearing filter
    filtered_df = smearing_filter(adjusted_df, rt_tolerance, ccs_tolerance)

    print("\n[INFO] Filtered DataFrame:")
    print(filtered_df)


if __name__ == "__main__":
    main()
