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
    try:
        all_matches = run_heavy_halogen_kaufman_pipeline(cef_folder, pimms_file)
    except Exception as e:
        print(f"[ERROR] Failed in run_heavy_halogen_kaufman_pipeline: {e}")
        return pd.DataFrame()

    try:
        matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
        multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)

        if multi_peak_df.empty:
            print("[INFO] No multi-peak matches found. Aborting.")
            return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Failed to match or show multi-peak compounds: {e}")
        return pd.DataFrame()

    try:
        merged_df = merging_pimms_report_with_halogen_data(all_matches, multi_peak_df)
    except Exception as e:
        print(f"[ERROR] Failed to merge halogen and PIMMS report: {e}")
        return pd.DataFrame()

    return merged_df


def main():
    cef_folder = r"PIMMS v1.2\NTA\Serum\CEF_folder"
    pimms_file = r"PIMMS v1.2\Data_output\Serum.csv"
    final_df = run_full_halogen_merging_pipeline(cef_folder, pimms_file)
    final_df.to_csv("Serum_heavy_halogen_matches.csv", index=False)


if __name__ == "__main__":
    main()
