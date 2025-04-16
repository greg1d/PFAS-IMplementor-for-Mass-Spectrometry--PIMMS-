import pandas as pd
import os

# === Input files ===
cef_filename = "NIST SRM-1957 10.d.DeMP.csv"
cef_path = r"PIMMS v1.2\CEF_reading\testing"
full_data_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

# === Read CEF sample name and data ===
cef_file = os.path.join(cef_path, cef_filename)
cef_df = pd.read_csv(cef_file)
sample_name = os.path.splitext(cef_filename)[
    0
].strip()  # e.g. "NIST SRM-1957 10.d.DeMP"

# === Read the full data file and strip all column names
full_df = pd.read_csv(full_data_path)
full_df.columns = [col.strip() for col in full_df.columns]

# === Define core column range (columns D–H, index 3–7)
core_cols = full_df.columns[3:8].tolist()

# === Find matching sample column
if sample_name in full_df.columns:
    print(f"[INFO] Matched sample column: '{sample_name}'")
    selected_df = full_df[core_cols + [sample_name]]
else:
    raise ValueError(
        f"[ERROR] Sample column '{sample_name}' not found in full dataset."
    )

# === Output ===
print("\n=== Preview of Core + Sample Columns ===")
print(selected_df.head())

# Optional: Save
# selected_df.to_csv("core_plus_sample_matched.csv", index=False)
