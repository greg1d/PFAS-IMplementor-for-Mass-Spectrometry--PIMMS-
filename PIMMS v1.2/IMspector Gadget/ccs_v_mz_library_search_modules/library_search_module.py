import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
import pandas as pd
from ccs_v_mz_modules.CCS_mz_trend_analysis import mz_repeating_unit_analysis

# ✅ Ensure "IMspector Gadget" is in Python's module search path


# Define file paths
FILE_PATH = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
LIBRARY_PATH = "PIMMS v1.2/import folder/Library test file.csv"

# ✅ Define all available repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

# ✅ Select a subset of repeating units for analysis
SELECTED_UNITS = ["CF2"]  # Only screen against these
selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}


def stack_library_with_adjusted():
    """Loads, standardizes, and combines rows from adjusted_df and library_df into a single DataFrame."""

    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] Data file not found: {FILE_PATH}")
        return None
    LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

    if not os.path.exists(LIBRARY_PATH):
        print(f"[ERROR] Library file not found: {LIBRARY_PATH}")
        return None

    # Read both DataFrames
    adjusted_df = pd.read_csv(FILE_PATH)
    library_df = pd.read_csv(LIBRARY_PATH)

    # ✅ Define column mappings to match adjusted_df
    column_mapping = {
        "PrecursorMz": "m/z",
        "PrecursorCCS": "CCS",
        "PrecursorRT": "RT",
        "Name": "Match",
    }

    # ✅ Rename columns in library_df to match adjusted_df
    library_df = library_df.rename(columns=column_mapping)

    # ✅ Add missing columns in `library_df` and fill with "N/A"
    missing_columns = [
        col for col in adjusted_df.columns if col not in library_df.columns
    ]
    for col in missing_columns:
        library_df[col] = "N/A"  # Fill missing columns with a placeholder

    # ✅ Ensure column order matches
    library_df = library_df[adjusted_df.columns]

    if "Match Source" in adjusted_df.columns:
        library_df["Match Source"] = LIBRARY_MATCH_SOURCE  # Use extracted filename
    else:
        print("[WARNING] 'Match Source' column not found in adjusted_df.")

    # ✅ Stack the two DataFrames (Concatenation of Rows)
    stacked_df = pd.concat([adjusted_df, library_df], ignore_index=True)

    return stacked_df


def main():
    """Stacks the DataFrame and runs repeating unit analysis on selected units."""
    stacked_df = stack_library_with_adjusted()

    if stacked_df is None:
        print("[ERROR] Could not generate stacked DataFrame. Exiting.")
        return

    print(f"[INFO] Stacked DataFrame created with {len(stacked_df)} rows.")

    # ✅ Perform repeating unit analysis with selected repeating units
    print(
        f"[INFO] Running mz_repeating_unit_analysis using: {list(selected_repeating_units.keys())}"
    )
    mass_groups = mz_repeating_unit_analysis(
        stacked_df, repeating_units=list(selected_repeating_units.keys())
    )

    if mass_groups.empty:
        print("[WARNING] No homologous series detected. Exiting.")
        return

    # ✅ Print results preview
    print("\n[INFO] Repeating Unit Analysis - Preview:")
    print(mass_groups.head(10).to_string(index=False))  # Print first 10 rows


if __name__ == "__main__":
    main()
