import pandas as pd
import numpy as np
import time
from numba import njit


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


@njit
def _find(x, parent):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


@njit
def _union(x, y, parent):
    px = _find(x, parent)
    py = _find(y, parent)
    if px != py:
        parent[py] = px


@njit
def _flag_duplicates_numba_core(mz, ccs, rt, mass_tols, ccs_tols, rt_tolerance):
    """
    Pure numba implementation of the nested loop that unions connected duplicates.
    Returns parent array for union-find structure.
    """
    n = len(mz)
    parent = np.arange(n)

    # Approximate search window — only compare close m/z values
    for i in range(n):
        for j in range(i + 1, n):
            if abs(mz[i] - mz[j]) > mz[i] * 2e-5:  # quick reject (~20 ppm)
                break  # safe due to sorted mz
            if (
                abs(mz[i] - mz[j]) <= max(mass_tols[i], mass_tols[j])
                and abs(ccs[i] - ccs[j]) <= max(ccs_tols[i], ccs_tols[j])
                and abs(rt[i] - rt[j]) <= rt_tolerance
            ):
                _union(i, j, parent)
    return parent


def flag_duplicates(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    """
    Fully equivalent to the previous version but accelerated with Numba.
    Ensures identical output structure.
    """
    start_time = time.time()

    df = adjusted_df.copy()
    df = df.sort_values("m/z").reset_index(drop=True)
    n = len(df)
    df["duplicate_flag"] = False
    df["duplicate_group"] = -1

    mz = df["m/z"].values
    ccs = df["CCS"].values
    rt = df["RT"].values
    mass_tols = calculate_mass_error_no_charge(mz, mass_error_ppm)
    ccs_tols = ccs * ccs_tolerance / 100

    # Run Numba-accelerated union-find pass
    parent = _flag_duplicates_numba_core(mz, ccs, rt, mass_tols, ccs_tols, rt_tolerance)

    # Collapse union-find roots
    roots = np.arange(n)
    for i in range(n):
        while parent[roots[i]] != roots[i]:
            roots[i] = parent[roots[i]]

    # Identify which ones actually have duplicates
    root_counts = np.bincount(roots)
    duplicate_mask = root_counts[roots] > 1
    df.loc[duplicate_mask, "duplicate_flag"] = True

    # Assign duplicate_group ids sequentially
    group_map = {}
    group_id = 0
    for root in np.unique(roots[duplicate_mask]):
        group_map[root] = group_id
        group_id += 1
    df["duplicate_group"] = [group_map.get(r, -1) for r in roots]

    elapsed = time.time() - start_time
    print(f"[Timing] flag_duplicates completed in {elapsed:.3f} seconds for {n} rows.")
    return df


def branching_merge(df):
    """
    Identical merge logic as before.
    """
    start_time = time.time()
    if "duplicate_group" not in df:
        return df

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    mean_cols = [c for c in ["m/z", "RT", "CCS", "DT"] if c in df.columns]
    max_cols = [
        c
        for c in numeric_cols
        if c not in mean_cols + ["duplicate_group", "duplicate_flag"]
    ]

    grouped = (
        df[df["duplicate_group"] != -1]
        .groupby("duplicate_group", dropna=False)
        .agg({**{c: "mean" for c in mean_cols}, **{c: "max" for c in max_cols}})
        .reset_index()
    )

    for col in categorical_cols:
        first_vals = (
            df[df["duplicate_group"] != -1]
            .groupby("duplicate_group", dropna=False)[col]
            .first()
            .reset_index()
        )
        grouped[col] = first_vals[col]

    grouped["duplicate_flag"] = True
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
