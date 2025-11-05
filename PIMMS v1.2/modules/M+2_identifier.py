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


def flag_two_four_mz_matches(df, mass_tols, ccs_tols, rt_tolerance):
    df = df.sort_values("m/z").reset_index(drop=True)
    flags = find_exact_mz_targets(
        df["m/z"].values,
        df["CCS"].values,
        df["RT"].values,
        mass_tols,
        ccs_tols,
        rt_tolerance,
    )
    df["flag_2_4_mz_match"] = flags
    return df


def main():
    # --- Define tolerances ---
    mass_tols = 0.005  # m/z tolerance
    ccs_tols = 0.02  # CCS tolerance
    rt_tolerance = 0.05  # RT tolerance

    df = pd.read_csv("PIMMS v1.2/PIMMS output/testing output.csv")

    # --- Run matching ---
    df_flagged = flag_two_four_mz_matches(df, mass_tols, ccs_tols, rt_tolerance)

    print("\n=== Input Data ===")
    print(df)
    print("\n=== Flagged Data ===")
    print(df_flagged[df_flagged["flag_2_4_mz_match"] == True])


if __name__ == "__main__":
    main()
