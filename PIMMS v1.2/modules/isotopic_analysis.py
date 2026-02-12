import numpy as np


def heavy_halogen_hunter(df):
    """
    Checks each row for an M+2 isotopic signature characteristic of Cl or Br,
    and adds a column with the raw M+2/M isotopic ratio.
    Includes debug statements to trace execution.
    """
    print("\n--- DEBUG: Starting Heavy Halogen Hunter ---")

    # 1. Check Input Data
    if df.empty:
        print("[DEBUG] Input DataFrame is empty. Returning immediately.")
        return df

    print(f"[DEBUG] Processing {len(df)} rows.")

    # Check if required columns exist
    required_cols = ["Intensity_1", "Intensity_3"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing required columns for isotopic analysis: {missing}")
        return df

    # Print sample of input intensities to verify data integrity
    print("[DEBUG] Sample Input Intensities (first 5 rows):")
    print(df[required_cols].head())

    # --- Calculate the ratio ---
    # Initialize with NaN
    df["M/M+2 Distribution"] = np.nan

    # Create mask
    safe_division_mask = df["Intensity_1"] > 0
    print(
        f"[DEBUG] Rows safe for division (Intensity_1 > 0): {safe_division_mask.sum()}"
    )

    # Perform calculation
    df.loc[safe_division_mask, "M/M+2 Distribution"] = (
        df.loc[safe_division_mask, "Intensity_3"]
        / df.loc[safe_division_mask, "Intensity_1"]
    )

    # Debug the calculated ratios
    print("[DEBUG] Calculated M/M+2 Ratios (first 5 rows):")
    print(df[["Intensity_1", "Intensity_3", "M/M+2 Distribution"]].head())

    # Check max ratio to see if threshold (0.28) is ever met
    max_ratio = df["M/M+2 Distribution"].max()
    print(f"[DEBUG] Max M/M+2 Ratio found in dataset: {max_ratio}")

    # --- Apply Logic ---
    conditions = [
        df["M/M+2 Distribution"] > 0.28,
        (df["Intensity_3"] == 0) | (df["Intensity_3"].isna()),
    ]

    choices = [
        "Potential Cl, Br present",
        "No M+2 peak detected - insufficient signal",
    ]

    default_choice = "No Cl or Br isotopic pattern detected"

    # Create classification column
    df["Isotopic_analysis"] = np.select(conditions, choices, default=default_choice)

    # --- Final Summary ---
    print("[DEBUG] Isotopic Analysis Results Summary:")
    print(df["Isotopic_analysis"].value_counts())
    print("--- DEBUG: End Heavy Halogen Hunter ---\n")

    return df
