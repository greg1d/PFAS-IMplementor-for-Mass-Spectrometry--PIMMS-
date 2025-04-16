import pandas as pd
import os
import glob
import xml.etree.ElementTree as ET


def get_cef_sample_names(cef_folder):
    """
    Returns a list of sample names (without extension) from all `.cef` files in the folder.
    """
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    sample_names = [os.path.splitext(os.path.basename(f))[0].strip() for f in cef_files]
    return sample_names


def get_cef_path(sample_name, cef_folder):
    """
    Finds and returns the full path to a .cef file that matches the sample_name.
    """
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    for path in cef_files:
        base = os.path.splitext(os.path.basename(path))[0].strip()
        if base == sample_name.strip():
            return path
    raise FileNotFoundError(
        f"[ERROR] No matching .cef file found for sample: '{sample_name}'"
    )


def extract_filtered_sample_data(sample_name, pimms_file_path):
    """
    For a given sample_name, extracts core columns + the matching sample column
    from the PIMMS dataset where values > 0.
    """
    pimms_df = pd.read_csv(pimms_file_path)
    pimms_df.columns = [col.strip() for col in pimms_df.columns]
    core_cols = pimms_df.columns[3:8].tolist()

    if sample_name not in pimms_df.columns:
        print(f"[WARN] Sample column '{sample_name}' not found in PIMMS data.")
        return None

    filtered_df = pimms_df[pimms_df[sample_name] > 0].copy()
    return filtered_df[core_cols + [sample_name]]


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


def print_PIMMS_report(sample_name, pimms_file_path):
    """
    Extracts and prints the filtered PIMMS report for a given sample.
    Only rows where sample intensity > 0 are included.
    """
    try:
        df = extract_filtered_sample_data(sample_name, pimms_file_path)
        if df is not None and not df.empty:
            print(f"\n=== PIMMS Report for Sample: {sample_name} ===")
            print(df.to_string(index=False))
        else:
            print(f"[INFO] No non-zero intensity rows found for: {sample_name}")
    except ValueError as e:
        print(f"[ERROR] {e}")


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
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set test.csv"

    sample_names = get_cef_sample_names(cef_folder)

    for sample_name in sample_names:
        print_sample_and_cef_report(sample_name, cef_folder, pimms_file_path)
        print_PIMMS_report(sample_name, pimms_file_path)  # this prints it already


if __name__ == "__main__":
    main()
