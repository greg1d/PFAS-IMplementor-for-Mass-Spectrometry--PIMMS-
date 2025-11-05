import numpy as np
import pandas as pd
from numba import njit


@njit
def find_exact_mz_targets(mz, ccs, rt, mz_tol, ccs_tol, rt_tol):
    n = len(mz)
    flag = np.zeros(n, dtype=np.bool_)

    for i in range(n):
        targets = [mz[i] + 2.0, mz[i] + 4.0]  # exact targets
        for target in targets:
            lower = target - mz_tol
            upper = target + mz_tol

            for j in range(i + 1, n):
                if mz[j] > upper:
                    break
                if mz[j] < lower:
                    continue

                if abs(ccs[i] - ccs[j]) <= ccs_tol and abs(rt[i] - rt[j]) <= rt_tol:
                    flag[j] = True
    return flag


def remove_Cl_Br_M2_signal(df, mass_tols, ccs_tols, rt_tolerance):
    # Sort for proper comparison
    df = df.sort_values("m/z").reset_index(drop=True)

    # Flag rows with m/z +2 or +4 matches
    flags = find_exact_mz_targets(
        df["m/z"].values,
        df["CCS"].values,
        df["RT"].values,
        mass_tols,
        ccs_tols,
        rt_tolerance,
    )

    df["flag_2_4_mz_match"] = flags

    # Remove flagged rows and return
    return (
        df[~df["flag_2_4_mz_match"]]
        .drop(columns=["flag_2_4_mz_match"])
        .reset_index(drop=True)
    )


def main():
    # --- Define tolerances ---
    mass_tols = 0.005  # m/z tolerance
    ccs_tols = 0.02  # CCS tolerance
    rt_tolerance = 0.5  # RT tolerance

    # --- Load data ---
    df = pd.read_csv("PIMMS v1.2/PIMMS output/testing output.csv")
    print(len(df))
    # --- Flag & remove matches ---
    df_cleaned = remove_Cl_Br_M2_signal(df, mass_tols, ccs_tols, rt_tolerance)
    print(len(df_cleaned))

    print("\n=== Cleaned Data ===")
    print(df_cleaned)


if __name__ == "__main__":
    main()
