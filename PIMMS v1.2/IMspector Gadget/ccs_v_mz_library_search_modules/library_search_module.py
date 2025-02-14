import os
import sys

import pandas as pd

# Get the absolute path of the "IMspector Gadget" directory
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.append(base_dir)  # Add base dir to Python path


from ccs_v_mz_modules.CCS_mz_trend_analysis import (
    CCS_v_mz_analysis,
    mz_repeating_unit_analysis,
)


def main():
    """User selects a library, and trend analysis is performed on the data."""

    # User input for the library file
    file_path = input("Enter the path to the data file (CSV format): ").strip()

    if not os.path.exists(file_path):
        print("[ERROR] File not found. Please provide a valid path.")
        return

    # Read input DataFrame
    adjusted_df = pd.read_csv(file_path)

    # User specifies repeating units to search for
    repeating_units = (
        input("Enter repeating units to analyze (comma-separated, e.g., CF2, OCF2): ")
        .strip()
        .split(",")
    )
    repeating_units = [unit.strip() for unit in repeating_units]

    # Perform repeating unit analysis
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    if mass_groups.empty:
        print("[INFO] No homologous series detected. Exiting.")
        return

    # Apply trend analysis on each group
    results = mass_groups.groupby("GroupID", group_keys=False).apply(
        lambda group: CCS_v_mz_analysis(
            group.drop(columns=["GroupID"], errors="ignore")
        )
    )

    # Save results to a file
    output_path = os.path.join(os.path.dirname(file_path), "trend_analysis_results.csv")
    results.to_csv(output_path, index=False)

    print(f"[INFO] Analysis complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()
