import pandas as pd
import numpy as np


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


def flag_duplicates(
    adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=0.5
):
    """
    Flag rows that are duplicates based on:
      - m/z ± ppm
      - CCS ± % tolerance
      - RT ± rt_tolerance (same units as RT column)
    Adds:
      - duplicate_flag: True if part of any duplicate group
      - duplicate_group: unique integer for each duplicate cluster
    """
    df = adjusted_df.copy()
    df["duplicate_flag"] = False
    df["duplicate_group"] = -1  # -1 means not in a duplicate group

    # Extract arrays
    mz = df["m/z"].values
    ccs = df["CCS"].values
    rt = df["RT"].values
    n = len(df)

    # Union-Find setup for connected components
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

    # Compare each row with every other row
    for i in range(n):
        mass_tol_i = calculate_mass_error_no_charge(mz[i], mass_error_ppm)
        ccs_tol_i = ccs[i] * ccs_tolerance / 100
        for j in range(i + 1, n):
            mass_tol_j = calculate_mass_error_no_charge(mz[j], mass_error_ppm)
            ccs_tol_j = ccs[j] * ccs_tolerance / 100

            if (
                abs(mz[i] - mz[j]) <= max(mass_tol_i, mass_tol_j)
                and abs(ccs[i] - ccs[j]) <= max(ccs_tol_i, ccs_tol_j)
                and abs(rt[i] - rt[j]) <= rt_tolerance
            ):
                df.loc[[i, j], "duplicate_flag"] = True
                union(i, j)

    # Assign duplicate groups
    group_map = {}
    group_id = 0
    for i in range(n):
        if df.loc[i, "duplicate_flag"]:
            root = find(i)
            if root not in group_map:
                group_map[root] = group_id
                group_id += 1
            df.loc[i, "duplicate_group"] = group_map[root]

    return df


def main():
    adjusted_df = pd.read_csv("duplicate row removal testing - Copy.csv")
    flagged_df = flag_duplicates(adjusted_df)
    print(flagged_df)


if __name__ == "__main__":
    main()
