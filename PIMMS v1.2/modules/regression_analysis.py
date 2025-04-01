import os
import sys

import pandas as pd

# Append the path to the 'CCSRT v mz predictions' folder
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "CCSRT v mz predictions")
)
if module_path not in sys.path:
    sys.path.append(module_path)

# Import your model functions
from quantile_regression_model_CCS import run_CCS_regression_analysis
from quantile_regression_model_RT import run_RT_regression_analysis


def exclude_rt_values(adjusted_df, rt_bounds_df):
    """
    Exclude rows in adjusted_df where the RT is outside the 5th–95th percentile band for its m/z.

    Parameters:
        adjusted_df (pd.DataFrame): Must include 'PrecursorMz' and 'RT' columns.
        rt_bounds_df (pd.DataFrame): Must include 'PrecursorMz', 'q05', 'q95' columns.

    Returns:
        pd.DataFrame: Filtered DataFrame with out-of-bound RT rows excluded.
    """
    merged = pd.merge(adjusted_df, rt_bounds_df, on="PrecursorMz", how="left")
    filtered = merged[
        (merged["RT"] >= merged["q05"]) & (merged["RT"] <= merged["q95"])
    ].copy()
    return filtered


def main():
    # File paths
    library_file = (
        r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
    )
    # Run quantile regression on CCS (doesn't need to return anything for this use case)
    print("\nRunning Quantile Regression on CCS...")
    ccs_eq = run_CCS_regression_analysis(library_file)
    print(ccs_eq)
    RT_eq = run_RT_regression_analysis(library_file)
    print(RT_eq)


if __name__ == "__main__":
    main()
