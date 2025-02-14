import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
import pandas as pd
from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)

# Define file paths
FILE_PATH = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
LIBRARY_PATH = "PIMMS v1.2/import folder/Library test file 1.csv"

# ✅ Extract the filename without extension for "Match Source"
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]

# ✅ Define all available repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

# ✅ Select a subset of repeating units for analysis
SELECTED_UNITS = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]
selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}


def external_mz_library_matching(IM_group, library_match_source):
    """
    Filters IM_group to retain only groups where at least 2 rows come from the external library file.

    Parameters:
    - IM_group (pd.DataFrame): Data containing identified homologous series.
    - library_match_source (str): The dynamically extracted standards library filename.

    Returns:
    - pd.DataFrame: Filtered IM_group containing only valid groups.
    """
    if IM_group.empty:
        print("[WARNING] IM_group is empty. No filtering applied.")
        return IM_group

    valid_groups = []

    # ✅ Group by GroupID
    for group_id, group_df in IM_group.groupby("GroupID"):
        # ✅ Count how many rows come from the specified external file
        source_count = (group_df["Match Source"] == library_match_source).sum()

        # ✅ Keep groups that have at least 2 rows from the external file
        if source_count >= 2:
            valid_groups.append(group_df)

    # ✅ Combine all valid groups into a new DataFrame
    if valid_groups:
        filtered_IM_group = pd.concat(valid_groups, ignore_index=True)
        print(f"[INFO] {len(filtered_IM_group)} rows retained after filtering.")
    else:
        filtered_IM_group = pd.DataFrame()
        print("[WARNING] No groups met the criteria of at least 2 library matches.")

    return filtered_IM_group


def stack_library_with_adjusted():
    """Loads, standardizes, and combines rows from adjusted_df and library_df into a single DataFrame."""

    if not os.path.exists(FILE_PATH):
        print(f"[ERROR] Data file not found: {FILE_PATH}")
        return None

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

    # ✅ Assign "Match Source" column
    if "Match Source" in adjusted_df.columns:
        library_df["Match Source"] = LIBRARY_MATCH_SOURCE  # Use extracted filename
    else:
        print("[WARNING] 'Match Source' column not found in adjusted_df.")

    # ✅ Stack the two DataFrames (Concatenation of Rows)
    stacked_df = pd.concat([adjusted_df, library_df], ignore_index=True)

    return stacked_df


def main():
    """Stacks the DataFrame, updates Match Source, runs repeating unit analysis, and performs CCS_v_mz_analysis."""
    stacked_df = stack_library_with_adjusted()

    if stacked_df is None:
        print("[ERROR] Could not generate stacked DataFrame. Exiting.")
        return

    print(f"[INFO] Stacked DataFrame created with {len(stacked_df)} rows.")

    # ✅ Extract dynamically the standards library filename (no extension)
    library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]
    print(f"[INFO] Using standards library: {library_match_source}")

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

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")

    # ✅ Run CCS_v_mz_analysis for each GroupID
    for group_id, group_df in mass_groups.groupby("GroupID"):
        print(f"\n[DEBUG] Analyzing Group {group_id}...")

        # **Run analysis**
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # ✅ Convert IM_group tuples back to DataFrame with metadata
        if IM_group:
            IM_group_df = group_df[
                group_df[["m/z", "CCS"]].apply(tuple, axis=1).isin(IM_group)
            ]
            print(f"\n[INFO] Significant IM_group detected for Group {group_id}:")

            # ✅ Print full metadata
            print(IM_group_df.to_string(index=False))

            # ✅ Apply `external_mz_library_matching` with the dynamically retrieved standards library name
            filtered_IM_group = external_mz_library_matching(
                IM_group_df, library_match_source
            )

            if not filtered_IM_group.empty:
                print(
                    f"\n[INFO] Valid IM_group found for Group {group_id} (Filtered Metadata):"
                )
                print(filtered_IM_group.to_string(index=False))


if __name__ == "__main__":
    main()
