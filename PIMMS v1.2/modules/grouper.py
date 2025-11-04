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


def branching_merge(df):
    """
    Merge rows based on duplicate_group:
      - For duplicate_group != -1:
          - mean of m/z, RT, CCS, DT
          - max of other numeric columns
          - first value of categorical columns
      - Rows with duplicate_group = -1 are unchanged
    """
    merged_rows = []

    # Identify numeric and categorical columns
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # Columns to take mean
    mean_cols = ["m/z", "RT", "CCS", "DT"]

    # Columns to take max = all numeric cols except the mean_cols
    max_cols = [
        c
        for c in numeric_cols
        if c not in mean_cols + ["duplicate_group", "duplicate_flag"]
    ]

    # Process each duplicate group
    for group_id in df["duplicate_group"].unique():
        if group_id == -1:
            continue
        group_df = df[df["duplicate_group"] == group_id]

        merged_row = {}
        # mean columns
        for col in mean_cols:
            merged_row[col] = group_df[col].mean()
        # max columns
        for col in max_cols:
            merged_row[col] = group_df[col].max()
        # categorical columns
        for col in categorical_cols:
            merged_row[col] = group_df[col].iloc[0]

        # Set duplicate_flag = True, duplicate_group = group_id
        merged_row["duplicate_flag"] = True
        merged_row["duplicate_group"] = group_id

        merged_rows.append(merged_row)

    # Create DataFrame for merged rows
    merged_df = pd.DataFrame(merged_rows)

    # Include non-duplicate rows unchanged
    non_duplicates = df[df["duplicate_group"] == -1].copy()

    final_df = pd.concat([non_duplicates, merged_df], ignore_index=True)

    # Optional: sort by original index or any column
    final_df = final_df.sort_values(by=["duplicate_group", "m/z"], ignore_index=True)

    return final_df


def main():
    adjusted_df = pd.read_csv("branching_filter_early_output.csv")
    flagged_df = flag_duplicates(adjusted_df)
    final_df = branching_merge(flagged_df)
    final_df.to_csv("duplicate row removal testing output.csv", index=False)


if __name__ == "__main__":
    main()
