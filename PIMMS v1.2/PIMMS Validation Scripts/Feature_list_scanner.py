import pandas as pd

# === File paths ===
features_file = (
    r"PIMMS Validation work\PIMMS data\All Features - No Blank Subtraction.csv"
)
targets_file = r"PIMMS Validation work\Target lists\Target_list_linear_only.csv"
skyline_file = r"PIMMS Validation work\Skyline comparison data\Detection_frequency_skyline_output_linear.csv"

# === Load data ===
features_df = pd.read_csv(features_file)
targets_df = pd.read_csv(targets_file)
skyline_df = pd.read_csv(skyline_file)


# === Normalize and build Name (Notes) for Skyline comparison ===
def build_name_notes(row):
    name = str(row["Name"]).strip()
    notes = (
        str(row["Notes"]).strip() if "Notes" in row and pd.notna(row["Notes"]) else ""
    )
    name = " ".join(name.split())  # Normalize whitespace
    notes = " ".join(notes.split())
    return f"{name} ({notes})" if notes and notes.lower() != "nan" else name


skyline_df["Name_Notes"] = skyline_df.apply(build_name_notes, axis=1)

# Rename columns for Skyline frequencies
skyline_df = skyline_df.rename(
    columns={
        "Detection Frequency (No blank subtraction, All samples)": "Skyline detection frequency - All Samples, No Blank Subtraction",
        "Detection Frequency (After Blank Subtraction, NIST Samples only)": "Skyline Sample Detection Frequency",
        "Skyline average intensity": "Skyline average intensity",
    }
)

skyline_names = set(skyline_df["Name_Notes"])

# Create dictionary mappings from Name (Notes)
skyline_freq_all_map = dict(
    zip(
        skyline_df["Name_Notes"],
        skyline_df["Skyline detection frequency - All Samples, No Blank Subtraction"],
    )
)
skyline_freq_sample_map = dict(
    zip(skyline_df["Name_Notes"], skyline_df["Skyline Sample Detection Frequency"])
)
skyline_intensity_map = dict(
    zip(skyline_df["Name_Notes"], skyline_df["Skyline average intensity"])
)

# === Rename target columns for consistency
targets_df = targets_df.rename(
    columns={
        "PrecursorMz": "m/z",
        "PrecursorCCS": "CCS",
        "PrecursorRT": "RT",
        "Molecule Name": "Molecule_Name",
    }
)

# === Initialize a list to store all matches
all_matches = []

# === Tolerance values
rt_tol = 0.2  # minutes
ccs_tol_pct = 0.02  # 2%
mz_tol = 15  # ppm
# === Perform matching
for idx, target in targets_df.iterrows():
    mz_tol_ppm = target["m/z"] * mz_tol / 1_000_000
    mz_min = target["m/z"] - mz_tol_ppm
    mz_max = target["m/z"] + mz_tol_ppm

    rt_min = target["RT"] - rt_tol
    rt_max = target["RT"] + rt_tol

    ccs_min = target["CCS"] * (1 - ccs_tol_pct)
    ccs_max = target["CCS"] * (1 + ccs_tol_pct)

    matches = features_df[
        (features_df["m/z"] >= mz_min)
        & (features_df["m/z"] <= mz_max)
        & (features_df["RT"] >= rt_min)
        & (features_df["RT"] <= rt_max)
        & (features_df["CCS"] >= ccs_min)
        & (features_df["CCS"] <= ccs_max)
    ].copy()

    # Consistent Name (Notes)
    molecule_name = str(target["Molecule_Name"]).strip()
    molecule_name = " ".join(molecule_name.split())
    notes = (
        str(target["Notes"]).strip()
        if "Notes" in target and pd.notna(target["Notes"])
        else ""
    )
    notes = " ".join(notes.split())
    name_with_notes = (
        f"{molecule_name} ({notes})"
        if notes and notes.lower() != "nan"
        else molecule_name
    )

    if not matches.empty:
        # Error metrics
        matches["MassError_ppm"] = (
            (matches["m/z"] - target["m/z"]) / target["m/z"]
        ) * 1e6
        matches["RT_Error"] = matches["RT"] - target["RT"]
        matches["CCS_Error_pct"] = (
            (matches["CCS"] - target["CCS"]) / target["CCS"]
        ) * 100
        matches["Name"] = name_with_notes

        # Detection frequency
        sample_cols = [col for col in matches.columns if "NIST" in col]

        def compute_freq(row, cols):
            values = row[cols]
            detected = (values > 0.001).sum()
            total = len(cols)
            return detected / total if total > 0 else None

        matches["Detection_Freq_Sample"] = matches.apply(
            lambda row: compute_freq(row, sample_cols), axis=1
        )

        matches["Detection_Frequency_blanks_+_samples"] = matches.apply(
            lambda row: compute_freq(row, sample_cols), axis=1
        )

        all_matches.append(matches)
    else:
        # === Create dummy row ===
        dummy_data = {
            "Name": name_with_notes,
            "ID": target.get("Row ID", "N/A"),
            "Feature List RT": "N/A",
            "RT Error": "N/A",
            "Feature List DT": "N/A",
            "Feature List CCS": "N/A",
            "CCS Error (%)": "N/A",
            "Feature List m/z": "N/A",
            "Mass Error (ppm)": "N/A",
            "Detection_Freq_Sample": 0,
            "Skyline detection frequency - All Samples, No Blank Subtraction": skyline_freq_all_map.get(
                name_with_notes, 0
            ),
        }

        for col in features_df.columns:
            if ".d" in col:
                dummy_data[col] = 0

        all_matches.append(pd.DataFrame([dummy_data]))
# === Post-processing after matching
if all_matches:
    final_df = pd.concat(all_matches, ignore_index=True)

    # Map Skyline detection frequencies and intensity to final_df
    final_df["Skyline detection frequency - All Samples, No Blank Subtraction"] = (
        final_df["Name"].map(skyline_freq_all_map)
    )
    final_df["Skyline Sample Detection Frequency"] = final_df["Name"].map(
        skyline_freq_sample_map
    )
    final_df["Skyline Average Intensity"] = final_df["Name"].map(skyline_intensity_map)
# === Round each specified column ===
rounding_map = {
    "Mass Error (ppm)": 3,
    "Detection_Freq_Sample": 2,
    "Skyline Sample Detection Frequency": 2,
    "Skyline detection frequency - All Samples, No Blank Subtraction": 2,
    "CCS Error (%)": 3,
}

# === Rename relevant columns ===
final_df = final_df.rename(
    columns={
        "ID": "Feature List Row ID",
        "RT": "Feature List RT",
        "CCS": "Feature List CCS",
        "DT": "Feature List DT" if "DT" in final_df.columns else "Feature List DT",
        "m/z": "Feature List m/z",
        "Row ID": "ID" if "Row ID" in final_df.columns else "ID",
        "RT_Error": "RT Error",
        "CCS_Error_pct": "CCS Error (%)",
        "MassError_ppm": "Mass Error (ppm)",
        "Skyline average intensity": "Skyline Average Intensity",
    }
)

# === Convert selected detection frequency columns to percentages ===
for col in [
    "Detection_Freq_Sample",
]:
    if col in final_df.columns:
        final_df[col] = final_df[col] * 100

# === Apply rounding ===
for col, decimals in rounding_map.items():
    if col in final_df.columns:
        final_df[col] = final_df[col].round(decimals)

# === Columns to keep and reorder ===
core_columns = [
    "Name",
    "Feature List Row ID",  # was "ID"
    "Feature List RT",
    "RT Error",
    "Feature List DT",
    "Feature List CCS",
    "CCS Error (%)",
    "Feature List m/z",
    "Mass Error (ppm)",
    "Detection_Freq_Sample",
    "Skyline detection frequency - All Samples, No Blank Subtraction",
]


# === Add all ".d" columns after core columns ===
d_cols = [col for col in final_df.columns if ".d" in col and col not in core_columns]
final_columns = core_columns + ["Skyline Average Intensity"] + d_cols

# === Subset only the selected columns ===
final_df = final_df[[col for col in final_columns if col in final_df.columns]]

# === Print rows in final_df with duplicate "Name" values ===
duplicates = final_df[final_df["Name"].duplicated(keep=False)]
core_info = duplicates[
    ["Name"] + [col for col in core_columns if col != "Name"]
].drop_duplicates("Name")

# === Get only .d columns (plus "Name" for context) ===
d_cols = [col for col in final_df.columns if ".d" in col]
subset = duplicates[["Name"] + d_cols]
max_d_values = duplicates[["Name"] + d_cols].groupby("Name", as_index=False).max()

merged = pd.merge(core_info, max_d_values, on="Name", how="left")


duplicates = final_df[final_df["Name"].duplicated(keep=False)]

# Core columns for info
core_columns = [
    "Name",
    "Feature List Row ID",
    "Feature List RT",
    "RT Error",
    "Feature List DT",
    "Feature List CCS",
    "CCS Error (%)",
    "Feature List m/z",
    "Mass Error (ppm)",
    "Detection_Freq_Sample",
    "Skyline detection frequency - All Samples, No Blank Subtraction",
    "Skyline Average Intensity",  # <-- Make sure it's here
]

# Extract unique core info per duplicate group
core_info = duplicates[
    ["Name"] + [col for col in core_columns if col != "Name"]
].drop_duplicates("Name")

# Get all .d columns
d_cols = [col for col in final_df.columns if ".d" in col]
max_d_values = duplicates[["Name"] + d_cols].groupby("Name", as_index=False).max()

# Merge core info + max .d values
merged = pd.merge(core_info, max_d_values, on="Name", how="left")

# Identify names of duplicate groups
duplicate_names = merged["Name"].unique()

# Get all other rows that aren't part of the duplicates
non_duplicates = final_df[~final_df["Name"].isin(duplicate_names)].copy()


# === Function to ensure all column names are unique before merging ===
def deduplicate_columns(columns):
    seen = {}
    new_cols = []
    for col in columns:
        if col not in seen:
            seen[col] = 1
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")
    return new_cols


# Deduplicate column names in both DataFrames
merged.columns = deduplicate_columns(merged.columns)
non_duplicates.columns = deduplicate_columns(non_duplicates.columns)

# Merge deduplicated + non-duplicate data
final_combined = pd.concat([merged, non_duplicates], ignore_index=True)

# Optional: reorder final columns
final_columns = core_columns + d_cols
final_combined = final_combined[
    [col for col in final_columns if col in final_combined.columns]
]

output_path = r"PIMMS Validation work\Comparison test output\Common Organic Molecules - profiler output with all features.csv"
final_combined.to_csv(output_path, index=False)
