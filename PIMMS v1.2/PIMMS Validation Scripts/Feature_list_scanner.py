import pandas as pd

# === File paths ===
features_file = r"PIMMS Validation work\PIMMS data\Debug file for testing.csv"
targets_file = r"PIMMS Validation work\Target_list.csv"

# === Load data ===
features_df = pd.read_csv(features_file)
targets_df = pd.read_csv(targets_file)

# Rename target columns for consistency
targets_df = targets_df.rename(
    columns={
        "PrecursorMz": "m/z",
        "PrecursorCCS": "CCS",
        "PrecursorRT": "RT",
        "Molecule Name": "Molecule_Name",
    }
)

# Define tolerance values
rt_tol = 0.2  # minutes
ccs_tol_pct = 0.02  # 2%

# Perform matching
for idx, target in targets_df.iterrows():
    mz_tol_ppm = target["m/z"] * 10 / 1_000_000  # 10 ppm window
    mz_min = target["m/z"] - mz_tol_ppm
    mz_max = target["m/z"] + mz_tol_ppm

    rt_min = target["RT"] - rt_tol
    rt_max = target["RT"] + rt_tol

    ccs_min = target["CCS"] * (1 - ccs_tol_pct)
    ccs_max = target["CCS"] * (1 + ccs_tol_pct)

    matches = features_df[
        (features_df["m/z"] >= mz_min)
        & (features_df["m/z"] <= mz_max)
        & (features_df["RT"] >= rt_min)
        & (features_df["RT"] <= rt_max)
        & (features_df["CCS"] >= ccs_min)
        & (features_df["CCS"] <= ccs_max)
    ].copy()

    if not matches.empty:
        print(f"\n--- Matches for Target [{idx}] {target['Molecule_Name']} ---")
        print(
            f"Target m/z: {target['m/z']:.6f}, RT: {target['RT']:.2f}, CCS: {target['CCS']:.2f}"
        )
        print(matches[["m/z", "RT", "CCS"]].to_string(index=False))
    else:
        print(f"\nNo match for Target [{idx}] {target['Molecule_Name']}")
