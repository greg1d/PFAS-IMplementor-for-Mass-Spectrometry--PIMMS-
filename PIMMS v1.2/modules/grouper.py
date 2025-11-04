import pandas as pd


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    return mass * mass_error_ppm * 1e-6


def flag_duplicates(adjusted_df, mass_error_ppm=10, ccs_tolerance=2.0, rt_tolerance=2):
    """
    Flag rows that are duplicates based on:
      - m/z ± ppm
      - CCS ± % tolerance
      - RT ± rt_tolerance (same units as RT column)
    """
    df = adjusted_df.copy()
    df["duplicate_flag"] = False

    # Extract arrays
    mz = df["m/z"].values
    ccs = df["CCS"].values
    rt = df["RT"].values
    n = len(df)

    # Compare each row with every other row (upper triangle)
    for i in range(n):
        mass_tol_i = calculate_mass_error_no_charge(mz[i], mass_error_ppm)
        ccs_tol_i = ccs[i] * ccs_tolerance / 100
        for j in range(i + 1, n):
            mass_tol_j = calculate_mass_error_no_charge(mz[j], mass_error_ppm)
            ccs_tol_j = ccs[j] * ccs_tolerance / 100

            # Check if all three criteria are satisfied
            if (
                abs(mz[i] - mz[j]) <= max(mass_tol_i, mass_tol_j)
                and abs(ccs[i] - ccs[j]) <= max(ccs_tol_i, ccs_tol_j)
                and abs(rt[i] - rt[j]) <= rt_tolerance
            ):
                df.loc[[i, j], "duplicate_flag"] = True

    return df


def main():
    adjusted_df = pd.read_csv("duplicate row removal testing - Copy.csv")
    flagged_df = flag_duplicates(adjusted_df)
    print(flagged_df)


if __name__ == "__main__":
    main()
