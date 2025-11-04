import time


import numpy as np


def smearing_filter(
    experimental_df,
    mz_col="m/z",
    rt_col="RT",
    ccs_col="CCS",
    rt_tolerance=0.5,
    ccs_tolerance=2,
):
    """
    Vectorized smearing filter to remove artifact peaks.

    Looks back at lower-mass peaks within mz-2, RT tolerance, and CCS tolerance,
    and zeros out higher-mass intensities if lower-mass peaks are >50x stronger.
    """
    start_total = time.perf_counter()

    if experimental_df.empty:
        print("[INFO] Input DataFrame is empty. Skipping smearing filter.")
        return experimental_df

    df_filtered = experimental_df.copy()

    # Dynamically identify sample columns (all columns in this example)
    sample_cols = [col for col in df_filtered.columns]

    # Validate required columns
    for col in [mz_col, rt_col, ccs_col]:
        if col not in df_filtered.columns:
            raise ValueError(f"Required column '{col}' not found in the DataFrame.")

    if not sample_cols:
        print("[WARNING] No sample columns found for smearing filter.")
        return df_filtered

    print(f"Applying smearing filter to sample columns: {sample_cols}")

    # Sort by m/z for efficient look-back search
    t0_sort = time.perf_counter()
    df_sorted = df_filtered.sort_values(mz_col).reset_index(drop=True)
    print(f"[TIME] Sorting by m/z: {time.perf_counter() - t0_sort:.4f} seconds")

    # Convert relevant columns to NumPy arrays for speed
    mz_arr = df_sorted[mz_col].values
    rt_arr = df_sorted[rt_col].values
    ccs_arr = df_sorted[ccs_col].values
    sample_arr = df_sorted[sample_cols].values  # shape (n_rows, n_samples)

    t0_core = time.perf_counter()

    for i in range(len(mz_arr)):
        mz1 = mz_arr[i]
        rt1 = rt_arr[i]
        ccs1 = ccs_arr[i]

        # Look-back window: mz_j in [mz1 - 2, mz1)
        left_idx = np.searchsorted(mz_arr, mz1 - 2, side="left")
        candidate_indices = np.arange(left_idx, i)
        if candidate_indices.size == 0:
            continue

        # Apply CCS and RT tolerances
        ccs_mask = (
            np.abs(ccs_arr[candidate_indices] - ccs1) / ccs1 * 100 < ccs_tolerance
        )
        rt_mask = np.abs(rt_arr[candidate_indices] - rt1) <= rt_tolerance
        valid_idx = candidate_indices[ccs_mask & rt_mask]

        if valid_idx.size == 0:
            continue

        # Vectorized intensity comparison across sample columns
        intensities_low = sample_arr[valid_idx, :]  # shape (num_candidates, n_samples)
        intensities_high = sample_arr[i, :]  # shape (n_samples,)
        mask_zero = (intensities_low > 50 * intensities_high).any(axis=0)
        sample_arr[i, mask_zero] = 0

        # Optional: progress tracking every 1000 rows
        if i > 0 and i % 1000 == 0:
            print(f"[INFO] Processed {i}/{len(mz_arr)} rows...")

    # Write back vectorized intensities to DataFrame
    df_sorted[sample_cols] = sample_arr

    print(f"[TIME] Core filtering logic: {time.perf_counter() - t0_core:.4f} seconds")
    print(
        f"[TIME] Total smearing filter: {time.perf_counter() - start_total:.4f} seconds"
    )
    print("✔️ Smearing filter applied.")

    return df_sorted
