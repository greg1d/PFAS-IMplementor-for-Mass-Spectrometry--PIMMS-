from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    get_cef_sample_names,
    run_matching_pipeline,
)
import pandas as pd


def compute_kaufman_constants(multi_peak_df):
    """
    Computes Kaufman C = (I2 / I1) * (1 / 0.011145) and derived metrics:
    - m / C
    - md / C (mass defect / C)

    Returns a DataFrame with all computed metrics per compound per sample.
    """
    kaufman_data = []

    grouped = multi_peak_df.groupby(["SourceFile", "Compound"])

    for (sample, compound_id), group in grouped:
        if len(group) < 2:
            continue

        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]
        mz2 = sorted_group.loc[1, "Peak_mz"]

        if intensity1 == 0:
            continue  # Avoid division by zero

        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)
        mass_defect = mz1 - round(mz1)

        kaufman_data.append(
            {
                "Sample": sample,
                "Compound": compound_id,
                "Peak_mz_1": mz1,
                "Intensity_1": intensity1,
                "Peak_mz_2": mz2,
                "Intensity_2": intensity2,
                "Kaufman_C": kaufman_C,
                "m_over_C": mz1 / kaufman_C,
                "mass_defect": mass_defect,
                "md_over_C": mass_defect / kaufman_C,
            }
        )

    return pd.DataFrame(kaufman_data)


def main():
    """
    Main function to load data and run the matching process.
    """
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"
    print("Loading PIMMS data...")
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = pimms_df.columns.str.strip()

    print("Parsing all CEF files...")
    all_cef_data = parse_all_cef_files_in_folder(cef_folder)

    sample_names = get_cef_sample_names(cef_folder)

    # 2. Run Pipeline to get a single DataFrame
    final_combined_df = run_matching_pipeline(
        pimms_df,
        all_cef_data,
        sample_names,
        mass_error_ppm=10,
        ccs_tolerance=2.0,
        rt_tolerance=1.0,
    )
    final_combined_df = compute_kaufman_constants(final_combined_df)
    print(final_combined_df)


if __name__ == "__main__":
    main()
