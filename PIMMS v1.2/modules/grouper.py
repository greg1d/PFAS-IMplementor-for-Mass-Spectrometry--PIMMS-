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

    for i in range(n):
        for j in range(i + 1, n):
            if abs(mz[i] - mz[j]) > mz[i] * 2e-5:  # ~20 ppm cutoff
                break  # safe due to sorted m/z
            if (
                abs(mz[i] - mz[j]) <= max(mass_tols[i], mass_tols[j])
                and abs(ccs[i] - ccs[j]) <= max(ccs_tols[i], ccs_tols[j])
                and abs(rt[i] - rt[j]) <= rt_tolerance
            ):
                _union(i, j, parent)
    return parent


def _flag_duplicates(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    """
    Core duplicate flagging and grouping.
    """
    start_time = time.time()

    df = adjusted_df.copy()
    df = df.sort_values("m/z").reset_index(drop=True)
    n = len(df)

    mz = df["m/z"].values
    ccs = df["CCS"].values
    rt = df["RT"].values
    mass_tols = calculate_mass_error_no_charge(mz, mass_error_ppm)
    ccs_tols = ccs * ccs_tolerance / 100

    # Run numba core
    parent = _flag_duplicates_numba_core(mz, ccs, rt, mass_tols, ccs_tols, rt_tolerance)

    # Collapse to roots
    roots = np.arange(n)
    for i in range(n):
        while parent[roots[i]] != roots[i]:
            roots[i] = parent[roots[i]]

    # Map duplicates
    root_counts = np.bincount(roots)
    duplicate_mask = root_counts[roots] > 1
    group_map = {r: idx for idx, r in enumerate(np.unique(roots[duplicate_mask]))}
    df["duplicate_group"] = [group_map.get(r, -1) for r in roots]

    elapsed = time.time() - start_time
    print(
        f"[Timing] Duplicate grouping completed in {elapsed:.3f} seconds for {n} rows."
    )
    return df


def _branching_merge(df):
    """
    Merges duplicate groups by averaging key metrics and removing duplicate columns.
    """
    start_time = time.time()

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    mean_cols = [c for c in ["m/z", "RT", "CCS", "DT"] if c in df.columns]
    max_cols = [c for c in numeric_cols if c not in mean_cols + ["duplicate_group"]]

    grouped = (
        df[df["duplicate_group"] != -1]
        .groupby("duplicate_group", dropna=False)
        .agg({**{c: "mean" for c in mean_cols}, **{c: "max" for c in max_cols}})
        .reset_index(drop=True)
    )

    for col in categorical_cols:
        grouped[col] = (
            df[df["duplicate_group"] != -1]
            .groupby("duplicate_group", dropna=False)[col]
            .first()
            .values
        )

    non_duplicates = df[df["duplicate_group"] == -1].copy()
    final_df = pd.concat([non_duplicates, grouped], ignore_index=True)
    final_df = final_df.sort_values(by=["m/z"], ignore_index=True)

    elapsed = time.time() - start_time
    print(f"[Timing] Merging completed in {elapsed:.3f} seconds.")
    return final_df.drop(columns=["duplicate_group"], errors="ignore")


def flag_and_merge_duplicates(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    """
    One-call interface for the full duplicate detection + merge workflow.
    Returns final merged DataFrame (no duplicate columns).
    """
    start_time = time.time()

    flagged_df = _flag_duplicates(
        adjusted_df, mass_error_ppm, ccs_tolerance, rt_tolerance
    )
    final_df = _branching_merge(flagged_df)

    elapsed = time.time() - start_time
    print(f"[Timing] Total flag_and_merge_duplicates runtime: {elapsed:.3f} seconds.")
    return final_df


def main():
    df = pd.read_csv("pre branching filter.csv")
    print(f"[Info] Loaded dataframe with {len(df)} rows.")
    final_df = flag_and_merge_duplicates(df)
    print(f"[Info] Final dataframe has {len(final_df)} rows.")
    print(final_df)


if __name__ == "__main__":
    main()
