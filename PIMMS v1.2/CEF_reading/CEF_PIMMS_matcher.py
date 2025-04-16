import pandas as pd
import os

# === Input files ===
cef_filename = "NIST SRM-1957 10.d.DeMP.csv"
cef_path = r"PIMMS v1.2\CEF_reading\testing"
PIMMS_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

# === Extract sample name from filename
sample_name = os.path.splitext(cef_filename)[0].strip()

# === Read PIMMS data and strip column names
pimms_df = pd.read_csv(PIMMS_file)
pimms_df.columns = [col.strip() for col in pimms_df.columns]

# === Define core column range (columns D–H, index 3–7)
core_cols = pimms_df.columns[3:8].tolist()

# === Check and filter by matching sample column
if sample_name in pimms_df.columns:
    print(f"[INFO] Matched sample column: '{sample_name}'")

    # Filter: only rows where sample intensity > 0
    filtered_df = pimms_df[pimms_df[sample_name] > 0].copy()

    # Select core + sample columns
    selected_df = filtered_df[core_cols + [sample_name]]
else:
    raise ValueError(f"[ERROR] Sample column '{sample_name}' not found in PIMMS data.")

# === Output ===
print("\n=== Filtered DataFrame Preview (sample > 0) ===")
print(selected_df)

# Optional: Save
# selected_df.to_csv("filtered_core_sample.csv", index=False)
