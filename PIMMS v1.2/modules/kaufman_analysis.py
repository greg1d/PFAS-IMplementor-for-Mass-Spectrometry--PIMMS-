import os
import sys

import pandas as pd

# Append the path to the 'CCSRT v mz predictions' folder
module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "CEF_reading")
)
if module_path not in sys.path:
    sys.path.append(module_path)

# Import your model functions
from pairing_CF2_and_heavy_halogens_with_PIMMS import (
    merging_pimms_report_with_halogen_data,
)
from heavy_halogen_hunter import run_heavy_halogen_kaufman_pipeline
from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF


def run_full_halogen_merging_pipeline(cef_folder, pimms_file):
    all_matches = run_heavy_halogen_kaufman_pipeline(cef_folder, pimms_file)
    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)

    if multi_peak_df.empty:
        print("[INFO] No multi-peak matches found. Aborting.")
        return pd.DataFrame()

    merged_df = merging_pimms_report_with_halogen_data(all_matches, multi_peak_df)
    return merged_df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    final_df = run_full_halogen_merging_pipeline(cef_folder, pimms_file)


if __name__ == "__main__":
    main()
