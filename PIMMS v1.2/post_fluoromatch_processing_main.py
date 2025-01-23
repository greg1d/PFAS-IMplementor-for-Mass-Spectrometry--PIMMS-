import os
import sys
import pandas as pd

# Add the modules and import directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))

from CCS_mz_trend_analysis import (
    CCS_vs_mz_trend_analysis,
    mz_repeating_unit_analysis,
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

    # Combine data from multiple files
    combined_data = pd.DataFrame()  # Initialize an empty DataFrame

    for file_path in file_paths:
        print(f"Loading data from {file_path}...")
        try:
            data = pd.read_csv(file_path)
            data["source_file"] = file_path  # Track the source of the data
            combined_data = pd.concat([combined_data, data], ignore_index=True)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if combined_data.empty:
        print("No data loaded. Exiting.")
        return

    # Save combined data to a temporary file (optional)
    temp_file_path = "temp_combined_data.csv"
    combined_data.to_csv(temp_file_path, index=False)
    print(f"Combined data saved to {temp_file_path}")

    # Perform mass repeating unit analysis
    print("\nPerforming mass repeating unit analysis...")
    groups = mz_repeating_unit_analysis(temp_file_path, mass_error_ppm, M_values)

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
            mz, row_id, ccs, score, sample_id = entry
            print(
                f"  m/z: {mz}, CCS: {ccs}, Score: {score}, Sample ID: {sample_id}, row.ID: {row_id}"
            )

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
