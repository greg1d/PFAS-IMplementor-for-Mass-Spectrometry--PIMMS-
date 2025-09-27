import numpy as np
import pandas as pd

# Import your model functions
from quantile_regression_model_CCS import run_CCS_regression_analysis
from quantile_regression_model_RT import run_RT_regression_analysis


def exclude_rt_values(adjusted_df, rt_eq):
    """
    Exclude rows where RT is outside the 5th–95th percentile range
    defined by log(m/z) regression equations.

    Parameters:
        adjusted_df (pd.DataFrame): Must include 'm/z' and 'RT' columns.
        rt_eq (dict): Dictionary with 'q05_slope', 'q05_intercept', 'q95_slope', 'q95_intercept'.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    log_mz = np.log(adjusted_df["m/z"])

    q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
    q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]

    filtered = adjusted_df[
        (adjusted_df["RT"] >= q05) & (adjusted_df["RT"] <= q95)
    ].copy()
    return filtered


def exclude_ccs_values(adjusted_df, CCS_eq):
    """
    Exclude rows where RT is outside the 5th–95th percentile range
    defined by log(m/z) regression equations.

    Parameters:
        adjusted_df (pd.DataFrame): Must include 'm/z' and 'RT' columns.
        rt_eq (dict): Dictionary with 'q05_slope', 'q05_intercept', 'q95_slope', 'q95_intercept'.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    log_mz = np.log(adjusted_df["m/z"])

    q05 = CCS_eq["q05_slope"] * log_mz + CCS_eq["q05_intercept"]
    q95 = CCS_eq["q95_slope"] * log_mz + CCS_eq["q95_intercept"]

    filtered = adjusted_df[
        (adjusted_df["CCS"] >= q05) & (adjusted_df["CCS"] <= q95)
    ].copy()
    return filtered


def produce_filtered_df(adjusted_df, library_file, rt_filter, ccs_filter):
    filtered_df = adjusted_df.copy()
    ccs_eq = run_CCS_regression_analysis(library_file)
    print("CCS equation:", ccs_eq)
    rt_eq = run_RT_regression_analysis(library_file)
    print("RT equation:", rt_eq)
    if rt_filter:
        log_mz = np.log(filtered_df["m/z"])
        rt_q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
        rt_q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]
        rt_mask = (filtered_df["RT"] >= rt_q05.values) & (
            filtered_df["RT"] <= rt_q95.values
        )
        filtered_df = filtered_df[rt_mask].copy()

    if ccs_filter:
        log_mz = np.log(filtered_df["m/z"])
        ccs_q05 = ccs_eq["q05_slope"] * log_mz + ccs_eq["q05_intercept"]
        ccs_q95 = ccs_eq["q95_slope"] * log_mz + ccs_eq["q95_intercept"]
        ccs_mask = (filtered_df["CCS"] >= ccs_q05.values) & (
            filtered_df["CCS"] <= ccs_q95.values
        )
        filtered_df = filtered_df[ccs_mask].copy()
    return filtered_df


def main():
    # File paths
    library_file = (
        r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
    )
    adjusted_path = r"PIMMS Validation work\PIMMS data\after_decay_filter.csv"

    # Load adjusted data
    adjusted_df = pd.read_csv(adjusted_path)

    rt_filter = True
    ccs_filter = True
    adjusted_df = produce_filtered_df(
        adjusted_df,
        library_file,
        rt_filter,
        ccs_filter,
    )


if __name__ == "__main__":
    main()
