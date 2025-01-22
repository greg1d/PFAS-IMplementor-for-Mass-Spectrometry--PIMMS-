import os
import sys

# Add the modules and import directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))

from CCS_mz_trend_analysis import CCS_vs_mz_trend_analysis, mz_repeating_unit_analysis
from repeating_units import TEST


def main():
    # File path to the CSV file
    file_path = "PIMMS v1.2/Dummy scored data.csv"
    mass_error_ppm = 10

    # User inputs for M values
    M_values = [TEST]  # Use CF2 and OCF2 directly

    # Call the CCS v mz analysis function
    groups = mz_repeating_unit_analysis(file_path, mass_error_ppm, M_values)

    # Call the function to print CCS values of the groups
    regression_results = CCS_vs_mz_trend_analysis(file_path, groups)

    # Print the regression results
    for group, results in regression_results.items():
        print(f"{group}:")
        print(f"  Slope: {results['slope']}")
        print(f"  Intercept: {results['intercept']}")
        print(f"  R-squared: {results['R_squared']}")
        print(f"  p-value: {results['p_value']}")
        print(f"  Standard Error: {results['std_err']}")


if __name__ == "__main__":
    main()
