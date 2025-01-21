import sys
import os

# Add the modules and import directories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))

from CCS_mz_trend_analysis import ccs_v_mz_analysis
from repeating_units import TEST


def main():
    # File path to the CSV file
    file_path = "PIMMS v1.2/Dummy test blank subtracted data.csv"
    mass_error_ppm = 10

    # User inputs for M values
    repeating_units = [TEST]  # Use CF2 and OCF2 directly

    # Call the CCS v mz analysis function
    ccs_v_mz_analysis(file_path, mass_error_ppm, repeating_units)


if __name__ == "__main__":
    main()
