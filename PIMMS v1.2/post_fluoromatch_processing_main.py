import os
import sys

# Add the modules and import directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))

from CCS_mz_trend_analysis import (
    CCS_vs_mz_trend_analysis,
    mz_repeating_unit_analysis,
    merge_and_extract_data,
)
from repeating_units import CF2, OCF2


def main():
    # File paths to the CSV files
    file_paths = [
        "data for visualizer/6988_fluoromatch_processed.csv",
        "data for visualizer/7974_fluoromatch_processed.csv",
    ]
    mass_error_ppm = 10

    # List and define available M values
    available_M_values = {
        "CF2": CF2,
        "OCF2": OCF2,
    }

    # Select the desired M value
    selected_M_values = ["CF2"]  # Example: Use CF2 for analysis
    M_values = [available_M_values[name] for name in selected_M_values]

    # Required columns for analysis
    required_columns = ["m/z", "Score", "CCS", "row.ID", "Name_or_Class"]

    # Merge and extract data from CSV files
    print("Merging and extracting data from files...")
    try:
        combined_data = merge_and_extract_data(file_paths, required_columns)
    except ValueError as e:
        print(f"Error during data merging: {e}")
        return

    # Debugging: Preview the combined dataset
    print("\nCombined Data Preview:")
    print(combined_data.head())

    # Perform mass repeating unit analysis
    print("\nPerforming mass repeating unit analysis...")
    groups = mz_repeating_unit_analysis(combined_data, mass_error_ppm, M_values)

    # Debugging: Print the first group for inspection
    if groups:
        print("\nFirst Group Debugging Output:")
        print(groups[0])
    else:
        print("No groups identified.")

    # Perform CCS vs m/z trend analysis and retrieve homologous series groups
    print("\nPerforming CCS vs m/z trend analysis...")
    homologous_series_groups = CCS_vs_mz_trend_analysis(
        groups, variation_threshold=0.02
    )

    # Print homologous series groups
    print("\nHomologous Series Groups:")
    for idx, group in enumerate(homologous_series_groups, start=1):
        print(f"Group {idx}:")
        for entry in group:
            mz, row_id, ccs, score, source_file, name_or_class = entry
            print(
                f"  m/z: {mz}, CCS: {ccs}, Score: {score}, Source File: {source_file}, row.ID: {row_id}, Name/Class: {name_or_class}"
            )

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
