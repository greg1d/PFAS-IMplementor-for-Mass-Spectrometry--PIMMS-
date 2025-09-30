import numpy as np

# Import your model functions
from quantile_regression_model_CCS import run_CCS_regression_analysis
from quantile_regression_model_RT import run_RT_regression_analysis


def exclude_rt_values(df, rt_eq, mz_col, rt_col):
    """
    Exclude rows where RT is outside the 5th–95th percentile range
    defined by log(m/z) regression equations.
    """
    # This function is already correct and needs no changes.
    log_mz = np.log(df[mz_col])
    q05 = rt_eq["q05_slope"] * log_mz + rt_eq["q05_intercept"]
    q95 = rt_eq["q95_slope"] * log_mz + rt_eq["q95_intercept"]
    filtered = df[(df[rt_col] >= q05) & (df[rt_col] <= q95)].copy()
    return filtered


def exclude_ccs_values(df, ccs_eq, mz_col, ccs_col):
    """
    Exclude rows where CCS is outside the 5th–95th percentile range
    defined by log(m/z) regression equations.
    """
    # This function is already correct and needs no changes.
    log_mz = np.log(df[mz_col])
    q05 = ccs_eq["q05_slope"] * log_mz + ccs_eq["q05_intercept"]
    q95 = ccs_eq["q95_slope"] * log_mz + ccs_eq["q95_intercept"]
    filtered = df[(df[ccs_col] >= q05) & (df[ccs_col] <= q95)].copy()
    return filtered


def produce_filtered_df(
    df,
    config,
    level_2_library,
    rt_regression_filter,
    ccs_regression_filter,
):
    """Apply RT and/or CCS regression filters to a pre-standardized DataFrame."""
    if df.empty:
        print("[INFO] Input DataFrame is empty. Skipping regression filters.")
        return df
    filtered_df = df.copy()

    # --- CHANGED: Remove the lookup from the config map ---
    # We now trust that the incoming 'df' has columns named 'm/z', 'RT', and 'CCS'.
    # This makes the logic much simpler.
    mz_col = "m/z"
    rt_col = "RT"
    ccs_col = "CCS"

    # We still need the clean map for the library file, as it's a separate file.
    try:
        clean_l2_map = config.clean_l2_map
    except KeyError:
        raise KeyError(
            "Config's clean_l2_map is missing. Check the translation step in your main workflow."
        )

    # --- Run analyses to get regression equations ---
    ccs_eq = run_CCS_regression_analysis(level_2_library, clean_l2_map)
    rt_eq = run_RT_regression_analysis(level_2_library, clean_l2_map)

    # --- Apply filters using the standard column names ---
    if rt_regression_filter:
        print("Applying RT regression filter...")
        initial_rows = len(filtered_df)
        filtered_df = exclude_rt_values(filtered_df, rt_eq, mz_col, rt_col)
        rows_removed = initial_rows - len(filtered_df)
        print(f"Removed {rows_removed} features based on RT regression filter.")

    if ccs_regression_filter:
        print("Applying CCS regression filter...")
        initial_rows = len(filtered_df)
        # This function is now called with the standard column name 'm/z'
        # which now exists in the filtered_df, resolving the error.
        filtered_df = exclude_ccs_values(filtered_df, ccs_eq, mz_col, ccs_col)
        rows_removed = initial_rows - len(filtered_df)
        print(f"Removed {rows_removed} features based on CCS regression filter.")

    return filtered_df
