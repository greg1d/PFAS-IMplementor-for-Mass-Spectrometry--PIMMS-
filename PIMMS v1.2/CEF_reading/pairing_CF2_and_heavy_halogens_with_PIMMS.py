from heavy_halogen_hunter import run_heavy_halogen_kaufman_pipeline
from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd


def merging_pimms_report_with_halogen_data(all_matches_df, multi_peak_df):
    """
    Merges the all_matches DataFrame with the multi-peak matched CEF results.

    Parameters:
        all_matches_df (pd.DataFrame): Result from heavy halogen analysis
        multi_peak_df (pd.DataFrame): Multi-peak matched CEF results

    Returns:
        pd.DataFrame: Merged DataFrame
    """
    if not {"SampleName", "Compound"}.issubset(all_matches_df.columns):
        raise ValueError("all_matches_df must contain 'SampleName' and 'Compound'")
    if not {"SampleName", "Compound"}.issubset(multi_peak_df.columns):
        raise ValueError("multi_peak_df must contain 'SampleName' and 'Compound'")

    merged = pd.merge(
        all_matches_df, multi_peak_df, on=["SampleName", "Compound"], how="inner"
    )

    print(
        f"[INFO] Merged dataset contains {merged.shape[0]} rows and {merged.shape[1]} columns."
    )
    return merged


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\import folder\Dummy test output.csv"
    all_matches = run_heavy_halogen_kaufman_pipeline(cef_folder, pimms_file)
    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak matches found. Aborting.")
        return pd.DataFrame()

    merged_df = merging_pimms_report_with_halogen_data(all_matches, multi_peak_df)
    merged_df.to_csv("merged_results.csv", index=False)


if __name__ == "__main__":
    main()
