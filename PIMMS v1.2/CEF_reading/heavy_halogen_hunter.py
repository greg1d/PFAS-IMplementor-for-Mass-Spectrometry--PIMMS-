from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd


def label_isotopic_peaks(df):
    """
    Labels isotopic peaks (M, M+1, M+2...) for each (SampleName, Compound) group.

    Parameters:
        df (pd.DataFrame): Must contain columns ['SampleName', 'Compound', 'Peak_mz']

    Returns:
        pd.DataFrame: Original dataframe with new column 'Isotope_Label'
    """
    if not {"SampleName", "Compound", "Peak_mz"}.issubset(df.columns):
        raise ValueError(
            "Input DataFrame must contain 'SampleName', 'Compound', and 'Peak_mz' columns."
        )

    df = df.copy()
    df["Isotope_Label"] = None

    grouped = df.groupby(["SampleName", "Compound"])

    for (sample, compound), group in grouped:
        sorted_group = group.sort_values("Peak_mz").reset_index()
        for i, idx in enumerate(sorted_group["index"]):
            df.at[idx, "Isotope_Label"] = f"M+{i}" if i > 0 else "M"

    return df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()
    print(multi_peak_df)

    labeled_df = label_isotopic_peaks(multi_peak_df)
    print(labeled_df)


if __name__ == "__main__":
    main()
