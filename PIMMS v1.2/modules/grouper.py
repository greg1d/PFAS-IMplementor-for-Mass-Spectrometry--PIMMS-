import pandas as pd
import numpy as np
import time


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


def flag_duplicates(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    """
    Optimized duplicate flagging with timing.
    """
    start_time = time.time()

    df = adjusted_df.copy()
    n = len(df)
    df["duplicate_flag"] = False
    df["duplicate_group"] = -1

    # Sort by m/z to limit comparisons
    df = df.sort_values("m/z").reset_index(drop=True)

    mz = df["m/z"].values
    ccs = df["CCS"].values
    rt = df["RT"].values

    # Precompute per-row tolerances
    mass_tols = calculate_mass_error_no_charge(mz, mass_error_ppm)
    ccs_tols = ccs * ccs_tolerance / 100

    parent = np.arange(n)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[py] = px

    # Compare only within local window of similar m/z
    mz_window = mz * mass_error_ppm * 2e-6  # rough double-tolerance window

    for i in range(n):
        # Limit search to rows whose m/z is within mass tolerance
        mz_diff = mz - mz[i]
        nearby = np.where(np.abs(mz_diff) <= mz_window[i])[0]

        # Compute subset differences
        ccs_diff = np.abs(ccs[nearby] - ccs[i])
        rt_diff = np.abs(rt[nearby] - rt[i])

        # Combine tolerance checks
        valid = (
            (np.abs(mz_diff[nearby]) <= np.maximum(mass_tols[i], mass_tols[nearby]))
            & (ccs_diff <= np.maximum(ccs_tols[i], ccs_tols[nearby]))
            & (rt_diff <= rt_tolerance)
        )

        # Union connected pairs
        for j in nearby[valid]:
            if i != j:
                df.loc[[i, j], "duplicate_flag"] = True
                union(i, j)

    # Assign duplicate groups efficiently
    roots = np.array([find(i) for i in range(n)])
    group_map = {
        r: idx for idx, r in enumerate(np.unique(roots[roots != np.arange(n)]))
    }
    df["duplicate_group"] = [group_map.get(r, -1) for r in roots]

    elapsed = time.time() - start_time
    print(f"[Timing] flag_duplicates completed in {elapsed:.3f} seconds for {n} rows.")
    return df


def branching_merge(df):
    """
    Merge rows based on duplicate_group with timing.
    """
    start_time = time.time()

    if "duplicate_group" not in df:
        return df

    # Identify numeric and categorical columns
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    mean_cols = [c for c in ["m/z", "RT", "CCS", "DT"] if c in df.columns]
    max_cols = [
        c
        for c in numeric_cols
        if c not in mean_cols + ["duplicate_group", "duplicate_flag"]
    ]

    # Grouping step – only for duplicate groups
    grouped = (
        df[df["duplicate_group"] != -1]
        .groupby("duplicate_group", dropna=False)
        .agg({**{c: "mean" for c in mean_cols}, **{c: "max" for c in max_cols}})
        .reset_index()
    )

    # Add categorical columns (take first)
    for col in categorical_cols:
        first_vals = (
            df[df["duplicate_group"] != -1]
            .groupby("duplicate_group", dropna=False)[col]
            .first()
            .reset_index()
        )
        grouped[col] = first_vals[col]

    grouped["duplicate_flag"] = True

    # Non-duplicates remain unchanged
    non_duplicates = df[df["duplicate_group"] == -1].copy()

    final_df = pd.concat([non_duplicates, grouped], ignore_index=True)
    final_df = final_df.sort_values(by=["duplicate_group", "m/z"], ignore_index=True)

    elapsed = time.time() - start_time
    print(f"[Timing] branching_merge completed in {elapsed:.3f} seconds.")
    return final_df


def main():
    total_start = time.time()

    adjusted_df = pd.read_csv("pre branching filter.csv")
    print(f"[Info] Loaded dataframe with {len(adjusted_df)} rows.")

    flagged_df = flag_duplicates(adjusted_df)
    final_df = branching_merge(flagged_df)

    total_elapsed = time.time() - total_start
    print(f"[Timing] Total runtime: {total_elapsed:.3f} seconds.")
    print(final_df)


if __name__ == "__main__":
    main()
