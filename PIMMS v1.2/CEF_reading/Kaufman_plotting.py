from CEF_matching_algorithm import match_PIMMS_to_CEF, compound_lookup, parse_cef_file
import os


def extract_multi_peak_compounds(cef_df):
    """
    Filters for compounds with more than one Peak_mz.
    """
    peak_counts = cef_df.groupby("Compound")["Peak_mz"].count()
    multi_peak_ids = peak_counts[peak_counts > 1].index
    return cef_df[cef_df["Compound"].isin(multi_peak_ids)].copy()


def show_multi_peak_compound_matches(matches, cef_folder):
    """
    For each sample, show compound lookups where matched compounds have >1 Peak_mz.
    """
    for sample_name, match_df in matches:
        print(f"\n>>> Showing compound peak info for sample: {sample_name}")

        # Load full CEF peak data for the sample
        cef_path = os.path.join(cef_folder, f"{sample_name}.cef")
        cef_df = parse_cef_file(cef_path)

        # Filter for compounds with >1 peak
        multi_peak_df = extract_multi_peak_compounds(cef_df)

        # Determine compound IDs that are both matched and have multiple peaks
        matched_ids = set(match_df["Compound"])
        multi_peak_ids = set(multi_peak_df["Compound"])
        valid_ids = matched_ids & multi_peak_ids

        for compound_id in sorted(valid_ids):
            compound_lookup(sample_name, cef_folder, int(compound_id))


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(
        cef_folder=cef_folder,
        pimms_file=pimms_file,
        mass_error_ppm=10,
        ccs_tolerance=2.0,
        rt_tolerance=1.0,
    )

    show_multi_peak_compound_matches(matches, cef_folder)


if __name__ == "__main__":
    main()
