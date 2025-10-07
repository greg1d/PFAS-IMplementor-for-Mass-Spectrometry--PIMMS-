import glob
import os
import xml.etree.ElementTree as ET

import pandas as pd


def get_cef_sample_names(cef_folder):
    """
    Returns a list of sample names (without extension) from all `.cef` files in the folder.
    """
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    sample_names = [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]
    return sample_names


def extract_filtered_sample_data(pimms_df):
    """
    Splits a PIMMS DataFrame into two DataFrames: one with sample
    intensity data and one with metadata.

    Args:
        pimms_df (pd.DataFrame): The input DataFrame containing all PIMMS data.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple containing two DataFrames:
                                           (sample_df, metadata_df).
    """
    # 1. Define the columns that constitute metadata
    metadata_cols = ["CCS", "m/z", "RT", "DT", "ID"]

    # Ensure all metadata columns exist in the DataFrame
    missing_cols = [col for col in metadata_cols if col not in pimms_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required metadata columns: {missing_cols}")

    # 2. Create the metadata_df by selecting only the metadata columns
    metadata_df = pimms_df[metadata_cols]

    # 3. Create the sample_df by dropping the metadata columns from the original DataFrame
    # This leaves all other columns, which are assumed to be sample intensity data.
    sample_df = pimms_df.drop(columns=metadata_cols)

    # 4. Return both DataFrames
    return sample_df, metadata_df


def parse_cef_file(cef_file_path):
    """
    Parses a .cef XML file and extracts peak information as a DataFrame.

    Returns a DataFrame with the following columns:
    - Compound
    - RT
    - DT
    - CCS
    - Peak_mz
    - m/z (lowest peak per compound)
    - Peak_intensity
    """
    tree = ET.parse(cef_file_path)
    root = tree.getroot()

    all_peaks = []
    compound_index = 1

    for compound in root.findall(".//Compound"):
        loc = compound.find("Location")
        if loc is None:
            continue

        rt = float(loc.attrib.get("rt", "nan"))

        ccs = float(loc.attrib.get("ccs", "nan"))
        dt = float(loc.attrib.get("dt", "nan"))

        peaks = compound.findall(".//MSPeaks/p")
        peak_mzs = [float(p.attrib.get("x", "nan")) for p in peaks]
        min_peak_mz = min(peak_mzs) if peak_mzs else float("nan")

        for peak in peaks:
            peak_data = {
                "Compound": compound_index,
                "RT": rt,
                "DT": dt,
                "CCS": ccs,
                "Peak_mz": float(peak.attrib.get("x", "nan")),
                "m/z": min_peak_mz,
                "Peak_intensity": float(peak.attrib.get("y", "nan")),
            }
            all_peaks.append(peak_data)

        compound_index += 1

    return pd.DataFrame(all_peaks)


def process_sample_matches(sample_names, pimms_file_path):
    """
    Processes each sample name, filters rows from the PIMMS dataset where values > 0,
    and returns a dictionary of sample_name → filtered DataFrame.
    """
    all_filtered = {}

    for sample_name in sample_names:
        print(f"\n[INFO] Processing sample: {sample_name}")
        filtered_df = extract_filtered_sample_data(sample_name, pimms_file_path)

        if filtered_df is not None and not filtered_df.empty:
            all_filtered[sample_name] = filtered_df
            # Optional: Save to file
            # filtered_df.to_csv(f"{sample_name}_filtered.csv", index=False)
        else:
            print(f"[SKIP] No data > 0 for sample: {sample_name}")

    return all_filtered


def print_sample_and_cef_report(sample_name, cef_folder, pimms_file_path):
    """
    Prints both the PIMMS report and CEF peak data for a given sample.
    """
    print(f"\n\n=== Report for Sample: {sample_name} ===")

    # Print PIMMS filtered data
    try:
        df = extract_filtered_sample_data(sample_name, pimms_file_path)
        if df is not None and not df.empty:
            print("\n--- PIMMS Report (non-zero intensities) ---")
            print(df.to_string(index=False))
        else:
            print("[INFO] No non-zero intensity rows found in PIMMS for this sample.")
    except ValueError as e:
        print(f"[ERROR] {e}")

    # Parse and print CEF data
    try:
        cef_path = get_cef_path(sample_name, cef_folder)
        cef_df = parse_cef_file(cef_path)
        if not cef_df.empty:
            print("\n--- CEF Peak Table ---")
            print(cef_df.to_string(index=False))
        else:
            print("[INFO] No peaks found in CEF file.")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")


def main():
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"

    pimms_df = pd.read_csv(pimms_file_path)
    sample_df, metadata_df = extract_filtered_sample_data(pimms_df)

    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"
    sample_names = get_cef_sample_names(cef_folder)
    print(sample_names)
    CEF_sample_information = parse_cef_file(cef_folder)
    print(CEF_sample_information)


if __name__ == "__main__":
    main()
