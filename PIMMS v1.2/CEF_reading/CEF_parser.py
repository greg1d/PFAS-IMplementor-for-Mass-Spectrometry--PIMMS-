import xml.etree.ElementTree as ET
import pandas as pd

# === File path ===
file_path = r"F:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS Validation work\Experimental Samples\NIST SRM-1957 1.d.DeMP.cef"

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
        continue  # Skip if no location info

    mz = float(loc.attrib.get("m", "nan"))
    rt = float(loc.attrib.get("rt", "nan"))
    rt_start = float(loc.attrib.get("rts", "nan"))
    rt_end = float(loc.attrib.get("rte", "nan"))
    area = float(loc.attrib.get("a", "nan"))
    height = float(loc.attrib.get("y", "nan"))
    ccs = float(loc.attrib.get("ccs", "nan"))
    dt = float(loc.attrib.get("dt", "nan"))

    score_elem = compound.find(".//CpdScore")
    score = (
        float(score_elem.attrib.get("score", "nan")) if score_elem is not None else None
    )

    # Extract peaks
    peaks = compound.findall(".//MSPeaks/p")
    for peak in peaks:
        peak_data = {
            "Compound": compound_index,
            "Peak_mz": float(peak.attrib.get("x", "nan")),
            "Peak_intensity": float(peak.attrib.get("y", "nan")),
            "Charge": int(peak.attrib.get("z", "1")),
            "Annotation": peak.attrib.get("s", ""),
            "Compound_mz": mz,
            "RT": rt,
            "RT_start": rt_start,
            "RT_end": rt_end,
            "Area": area,
            "Height": height,
            "CCS": ccs,
            "Drift_time": dt,
            "Score": score,
        }
        all_peaks.append(peak_data)

    compound_index += 1

# === Convert to DataFrame ===
peaks_df = pd.DataFrame(all_peaks)

# === Output ===
print("\n=== First 5 Peaks with Compound Index ===")
print(peaks_df.head())

# Optional: Save to file
# peaks_df.to_csv("cef_peaks_with_compound_index.csv", index=False)
