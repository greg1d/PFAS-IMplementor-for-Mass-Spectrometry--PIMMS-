import xml.etree.ElementTree as ET
import pandas as pd
import os
import glob


def parse_cef_file_from_folder(cef_folder):
    """
    Finds the first .cef file in the folder and parses it into a DataFrame.

    Returns:
        - peaks_df (DataFrame): peak-level info
        - sample_name (str): extracted from filename (no extension)
    """
    cef_files = glob.glob(os.path.join(cef_folder, "*.cef"))
    if not cef_files:
        raise FileNotFoundError(f"[ERROR] No .cef files found in: {cef_folder}")

    cef_path = cef_files[0]
    sample_name = os.path.splitext(os.path.basename(cef_path))[0].strip()

    tree = ET.parse(cef_path)
    root = tree.getroot()

    all_peaks = []
    compound_index = 1

    for compound in root.findall(".//Compound"):
        loc = compound.find("Location")
        if loc is None:
            continue

        rt = float(loc.attrib.get("rt", "nan"))
        rt_start = float(loc.attrib.get("rts", "nan"))
        rt_end = float(loc.attrib.get("rte", "nan"))
        ccs = float(loc.attrib.get("ccs", "nan"))
        dt = float(loc.attrib.get("dt", "nan"))

        score_elem = compound.find(".//CpdScore")
        score = (
            float(score_elem.attrib.get("score", "nan"))
            if score_elem is not None
            else None
        )

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

    peaks_df = pd.DataFrame(all_peaks)
    return peaks_df, sample_name


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"

    try:
        cef_peaks_df, sample_name = parse_cef_file_from_folder(cef_folder)
        print(f"[INFO] Parsed CEF file for sample: {sample_name}")
        print(cef_peaks_df.head())

        # Optional save
        # cef_peaks_df.to_csv(f"{sample_name}_peaks.csv", index=False)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
