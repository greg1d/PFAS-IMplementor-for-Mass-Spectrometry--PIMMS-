import os
import sys

# Add the modules and import directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))

from CCS_mz_trend_analysis import (
    CCS_vs_mz_trend_analysis,
    mz_repeating_unit_analysis,
)
from repeating_units import CF2, OCF2


def main():
    # File path to the CSV file
    file_path = "PIMMS v1.2/tests/Dummy scored data.csv"
    mass_error_ppm = 10

    # List and define available M values
    available_M_values = {
        "CF2": CF2,
        "OCF2": OCF2,
    }

    # Select the desired M value by modifying this line
    selected_M_values = ["CF2"]  # Example: Use CF2 for analysis
    M_values = [available_M_values[name] for name in selected_M_values]

    # Perform mass repeating unit analysis
    print("\nPerforming mass repeating unit analysis...")
    groups = mz_repeating_unit_analysis(file_path, mass_error_ppm, M_values)

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
            # Adjust to handle tuples
            mz, ccs, score, sample_id, row_id = entry
            print(
                f"  m/z: {mz}, CCS: {ccs}, Score: {score}, Sample ID: {sample_id}, row.ID: {row_id}"
            )

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
