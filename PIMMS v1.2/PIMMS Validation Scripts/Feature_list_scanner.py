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
        # Calculate error metrics
        matches["MassError_ppm"] = (
            (matches["m/z"] - target["m/z"]) / target["m/z"]
        ) * 1e6
        matches["RT_Error"] = matches["RT"] - target["RT"]
        matches["CCS_Error_pct"] = (
            (matches["CCS"] - target["CCS"]) / target["CCS"]
        ) * 100

        # Compose Name (Notes)
        name_with_notes = str(target["Molecule_Name"])
        if "Notes" in target:
            notes = str(target["Notes"]).strip()
            if notes and notes.lower() != "nan":
                name_with_notes += f" ({notes})"

        matches["Name"] = name_with_notes

        # === Detection Frequency Calculation ===
        sample_cols = [col for col in matches.columns if "NIST" in col]
        blank_cols = [col for col in matches.columns if "Method" in col]

        def compute_freq(row, cols):
            values = row[cols]
            detected = (values > 10).sum()
            total = len(cols)
            return detected / total if total > 0 else None

        matches["Detection_Freq_Sample"] = matches.apply(
            lambda row: compute_freq(row, sample_cols), axis=1
        )
        matches["Detection_Freq_Blank"] = matches.apply(
            lambda row: compute_freq(row, blank_cols), axis=1
        )

        # Primary detection frequency = sample detection frequency
        combined_cols = sample_cols + blank_cols
        matches["Detection_Frequency_blanks_+_samples"] = matches.apply(
            lambda row: compute_freq(row, combined_cols), axis=1
        )  # Reorder and print
        print(
            matches[
                [
                    "Name",
                    "m/z",
                    "RT",
                    "CCS",
                    "MassError_ppm",
                    "RT_Error",
                    "CCS_Error_pct",
                    "Detection_Freq_Sample",
                    "Detection_Frequency_blanks_+_samples",
                ]
            ].to_string(index=False, float_format="%.4f")
        )
