import numpy as np
import pandas as pd
from numba import njit


@njit
def find_exact_mz_targets(mz, ccs, rt, mass_error_ppm, ccs_tolerance_percent, rt_tol):
    n = len(mz)
    flag = np.zeros(n, dtype=np.bool_)

    for i in range(n):
        # Dynamic tolerances per feature
        mz_tol_i = mz[i] * mass_error_ppm * 1e-6
        ccs_tol_i = ccs[i] * ccs_tolerance_percent

        targets = [mz[i] + 2.0, mz[i] + 4.0]  # exact isotope targets

        for target in targets:
            lower = target - mz_tol_i
            upper = target + mz_tol_i

            for j in range(i + 1, n):
                if mz[j] > upper:
                    break
                if mz[j] < lower:
                    continue

                # compute per-j tolerances dynamically
                mz_tol_j = mz[j] * mass_error_ppm * 1e-6
                ccs_tol_j = ccs[j] * ccs_tolerance_percent

                if (
                    abs(ccs[i] - ccs[j]) <= max(ccs_tol_i, ccs_tol_j)
                    and abs(rt[i] - rt[j]) <= rt_tol
                ):
                    flag[j] = True
    return flag


def remove_Cl_Br_M2_signal(df, mass_error_ppm, ccs_tolerance_percent, rt_tolerance):
    # Sort for proper comparison
    df = df.sort_values("m/z").reset_index(drop=True)

    # Run isotopic pattern flagging (Numba)
    flags = find_exact_mz_targets(
        df["m/z"].values,
        df["CCS"].values,
        df["RT"].values,
        mass_error_ppm,
        ccs_tolerance_percent,
        rt_tolerance,
    )

    df["flag_2_4_mz_match"] = flags

    # Remove flagged rows and return
    cleaned_df = (
        df[~df["flag_2_4_mz_match"]]
        .drop(columns=["flag_2_4_mz_match"])
        .reset_index(drop=True)
    )
    return cleaned_df


def main():
    # --- Define tolerances ---
    mass_error_ppm = 10  # m/z tolerance in ppm
    ccs_tolerance_percent = 0.02  # CCS tolerance (2%)
    rt_tolerance = 0.5  # RT tolerance (units as in dataset)

    # --- Load data ---
    df = pd.read_csv("PIMMS v1.2/PIMMS output/testing output.csv")

    # --- Flag & remove matches ---
    df_cleaned = remove_Cl_Br_M2_signal(
        df, mass_error_ppm, ccs_tolerance_percent, rt_tolerance
    )


if __name__ == "__main__":
    main()
