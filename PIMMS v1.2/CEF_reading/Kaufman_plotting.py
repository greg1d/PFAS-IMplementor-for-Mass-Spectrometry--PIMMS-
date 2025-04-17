from CEF_matching_algorithm import match_PIMMS_to_CEF, compound_lookup, parse_cef_file
import os
import pandas as pd


def extract_multi_peak_compounds(cef_df):
    """Filters for compounds with more than one Peak_mz."""
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    multi_peak_ids = peak_counts[peak_counts > 1].index
    return cef_df[cef_df["Compound"].isin(multi_peak_ids)].copy()


def show_multi_peak_compound_matches(matches, cef_folder):
    """
    For each sample, show compound lookups where matched compounds have >1 Peak_mz.
    Returns a DataFrame of all matched multi-peak compounds with sample info.
    """
    all_multi_peaks = []

    for sample_name, match_df in matches:
        print(f"\n>>> Showing compound peak info for sample: {sample_name}")
        cef_path = os.path.join(cef_folder, f"{sample_name}.cef")
        cef_df = parse_cef_file(cef_path)

        multi_peak_df = extract_multi_peak_compounds(cef_df)

        matched_ids = set(match_df["Compound"])
        multi_peak_ids = set(multi_peak_df["Compound"])
        valid_ids = matched_ids & multi_peak_ids

        filtered_df = multi_peak_df[multi_peak_df["Compound"].isin(valid_ids)].copy()
        filtered_df["SampleName"] = sample_name  # Add sample identity
        all_multi_peaks.append(filtered_df)

        for compound_id in sorted(valid_ids):
            compound_lookup(sample_name, cef_folder, int(compound_id))

    if all_multi_peaks:
        return pd.concat(all_multi_peaks, ignore_index=True)
    else:
        return pd.DataFrame()


def compute_kaufman_constants(multi_peak_df):
    """
    Computes Kaufman C = (I2 / I1) * (1 / 0.011145) for multi-peak compounds,
    grouped by SampleName + Compound.
    """
    kaufman_data = []

    grouped = multi_peak_df.groupby(["SampleName", "Compound"])

    for (sample, compound_id), group in grouped:
        if len(group) < 2:
            continue

        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]
        mz2 = sorted_group.loc[1, "Peak_mz"]

        if intensity1 == 0:
            continue

        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)

        kaufman_data.append(
            {
                "Sample": sample,
                "Compound": compound_id,
                "Peak_mz_1": mz1,
                "Intensity_1": intensity1,
                "Peak_mz_2": mz2,
                "Intensity_2": intensity2,
                "Kaufman_C": kaufman_C,
            }
        )

    return pd.DataFrame(kaufman_data)


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)

    if not multi_peak_df.empty:
        kaufman_df = compute_kaufman_constants(multi_peak_df)
        print("\n=== Kaufman Plot Constants ===")
        print(kaufman_df.to_string(index=False))
    else:
        print("\n[INFO] No multi-peak compound matches to compute Kaufman constants.")


if __name__ == "__main__":
    main()
