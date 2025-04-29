from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
from Kaufman_plotting import compute_kaufman_constants, show_multi_peak_compound_matches
from CF2_prioritization import (
    compute_mCm_alignment,
    compute_MDCm_alignment,
    cf2_prioritization,
    plot_kaufman_scatter_colored,
)
from FC_prediction import FC_prediction


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    kaufman_df = compute_kaufman_constants(multi_peak_df)
    kaufman_df = compute_mCm_alignment(kaufman_df)
    kaufman_df = compute_MDCm_alignment(kaufman_df)
    kaufman_df = cf2_prioritization(kaufman_df)
    plot_kaufman_scatter_colored(kaufman_df)
    kaufman_df = FC_prediction(kaufman_df)
    print(kaufman_df)


if __name__ == "__main__":
    main()
