import xml.etree.ElementTree as ET
import pandas as pd

# === File path ===
file_path = r"F:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS Validation work\Experimental Samples\NIST SRM-1957 10.d.DeMP.cef"

# === Parse XML ===
tree = ET.parse(file_path)
root = tree.getroot()

# === Container for all peaks ===
all_peaks = []

# === Loop through compounds ===
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
        float(score_elem.attrib.get("score", "nan")) if score_elem is not None else None
    )

    peaks = compound.findall(".//MSPeaks/p")
    peak_mzs = [float(p.attrib.get("x", "nan")) for p in peaks]
    min_peak_mz = min(peak_mzs) if peak_mzs else float("nan")

    for peak in peaks:
        peak_data = {
            "Compound": compound_index,
            "RT": rt,
            "DT": dt,  # renamed from Drift_time
            "CCS": ccs,
            "Peak_mz": float(peak.attrib.get("x", "nan")),
            "m/z": min_peak_mz,  # renamed from Compound_mz
            "Peak_intensity": float(peak.attrib.get("y", "nan")),
        }
        all_peaks.append(peak_data)

    compound_index += 1

# === Convert to DataFrame ===
peaks_df = pd.DataFrame(all_peaks)

# === Output ===
print("\n=== First 5 Peaks with Renamed Columns ===")
print(peaks_df.head())

# Optional: Save
peaks_df.to_csv(
    r"PIMMS v1.2\CEF_reading\testing\cef_peaks_with_renamed_columns.csv", index=False
)
