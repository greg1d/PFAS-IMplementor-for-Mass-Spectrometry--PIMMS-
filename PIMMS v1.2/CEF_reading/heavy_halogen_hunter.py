from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
import re
import numpy as np
from Kaufman_plotting import compute_kaufman_constants
from CF2_prioritization import (
    compute_mCm_alignment,
    compute_MDCm_alignment,
    cf2_prioritization,
)
from FC_prediction import FC_prediction


def label_isotopic_peaks(df):
    """
    Labels isotopic peaks (M, M+1, M+2...) for each (SampleName, Compound) group.

    Parameters:
        df (pd.DataFrame): Must contain columns ['SampleName', 'Compound', 'Peak_mz']

    Returns:
        pd.DataFrame: Original dataframe with new column 'Isotope_Label'
    """
    if not {"SampleName", "Compound", "Peak_mz"}.issubset(df.columns):
        raise ValueError(
            "Input DataFrame must contain 'SampleName', 'Compound', and 'Peak_mz' columns."
        )

    df = df.copy()
    df["Isotope_Label"] = None

    grouped = df.groupby(["SampleName", "Compound"])

    for (sample, compound), group in grouped:
        sorted_group = group.sort_values("Peak_mz").reset_index()
        for i, idx in enumerate(sorted_group["index"]):
            df.at[idx, "Isotope_Label"] = f"M+{i}" if i > 0 else "M"

    return df


def normalize_isotopic_intensity(df):
    """
    Normalizes Peak_intensity in each (SampleName, Compound) group by the intensity of the M peak (maximum).

    Parameters:
        df (pd.DataFrame): Must contain 'SampleName', 'Compound', and 'Peak_intensity'

    Returns:
        pd.DataFrame: Original dataframe with an additional 'Normalized_Intensity' column
    """
    if not {"SampleName", "Compound", "Peak_intensity"}.issubset(df.columns):
        raise ValueError(
            "Input DataFrame must contain 'SampleName', 'Compound', and 'Peak_intensity' columns."
        )

    df = df.copy()
    df["Normalized_Intensity"] = df.groupby(["SampleName", "Compound"])[
        "Peak_intensity"
    ].transform(lambda x: x / x.max() if x.max() != 0 else 0)

    return df


"""
# Citations

- [DOI: 10.1351/PAC-REP-10-06-02](https://doi.org/10.1351/PAC-REP-10-06-02)
- J. S. Coursey, D. J. Schwab, J. J. Tsai, and R. A. Dragoset
- NIST Physical Measurement Laboratory
- [IOP Science Article](https://iopscience.iop.org/article/10.1088/1674-1137/36/12/003)
- [CIAAW Atomic Weights](https://www.ciaaw.org/atomic-weights.htm)
"""


def read_isotope_data(file_path):
    """Read the isotope data from the given file path."""
    with open(file_path, "r") as file:
        data = file.read()
    return data


def parse_isotope_data(data):
    """Parse the isotope data from the given string."""
    # Define regex patterns for each field
    patterns = {
        "Atomic Number": re.compile(r"Atomic Number = (\d+)"),
        "Atomic Symbol": re.compile(r"Atomic Symbol = (\w+)"),
        "Mass Number": re.compile(r"Mass Number = (\d+)"),
        "Relative Atomic Mass": re.compile(r"Relative Atomic Mass = ([\d.]+)"),
        "Isotopic Composition": re.compile(r"Isotopic Composition = ([\d.]+)"),
        "Standard Atomic Weight": re.compile(r"Standard Atomic Weight = ([\d.,\[\]]+)"),
        "Notes": re.compile(r"Notes = (\w*)"),
    }

    # Initialize lists to store the parsed data
    data_dict = {key: [] for key in patterns.keys()}

    # Split the data into lines
    lines = data.split("\n")

    # Process the lines in chunks corresponding to each data point
    chunk_size = 8  # Each data point is composed of 7 lines followed by a blank line
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]
        for key, pattern in patterns.items():
            for line in chunk:
                if line.strip() == "":
                    continue  # Skip blank lines
                match = pattern.search(line)
                if match:
                    value = match.group(1)
                    if key in ["Relative Atomic Mass", "Isotopic Composition"]:
                        value = re.sub(
                            r"\(.*\)", "", value
                        ).strip()  # Remove values in parentheses
                    if key == "Isotopic Composition" and value == "":
                        value = None  # Treat empty isotopic composition as None
                    data_dict[key].append(value)
                    break
            else:
                data_dict[key].append(None)  # Append None if no match is found

    # Debug: Print the parsed data dictionary

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data_dict)

    # Exclude rows with empty Isotopic Composition
    df = df[df["Isotopic Composition"].notna()]

    # Drop the Notes column
    df = df.drop(columns=["Notes"])

    return df


def add_elemental_symbol(df, csv_path):
    """Add the Elemental Symbol column to the DataFrame based on the Atomic Number."""
    # Read the CSV file
    atomic_numbers_df = pd.read_csv(csv_path)

    # Ensure both columns have the same data type
    df = df.dropna(subset=["Atomic Number"])  # Drop rows where Atomic Number is None
    df["Atomic Number"] = df["Atomic Number"].astype(int)
    atomic_numbers_df["AtomicNumber"] = atomic_numbers_df["AtomicNumber"].astype(int)

    # Merge the DataFrame with the atomic numbers DataFrame
    df = df.merge(
        atomic_numbers_df, left_on="Atomic Number", right_on="AtomicNumber", how="left"
    )

    # Rename the Symbol column to Elemental Symbol
    df = df.rename(columns={"Symbol": "Elemental Symbol"})

    # Drop the AtomicNumber column
    df = df.drop(columns=["AtomicNumber"])

    # Reorder columns to place Elemental Symbol as the second column
    cols = df.columns.tolist()
    cols.insert(1, cols.pop(cols.index("Elemental Symbol")))
    df = df[cols]

    return df


def heavy_halogen_reader(isotope_df):
    """
    Identify Br or Cl isotopic signatures based on normalized isotopic compositions.

    Parameters:
        isotope_df (pd.DataFrame): Contains reference isotopic distributions with:
                                   'Elemental Symbol', 'Relative Atomic Mass', 'Isotopic Composition'

    Returns:
        halogen_df (pd.DataFrame): Subset with Br/Cl isotopes, labeled and normalized
    """
    # Filter for Br and Cl
    halogen_df = isotope_df[isotope_df["Elemental Symbol"].isin(["Br", "Cl"])].copy()

    # Ensure correct types
    halogen_df["Relative Atomic Mass"] = halogen_df["Relative Atomic Mass"].astype(
        float
    )
    halogen_df["Isotopic Composition"] = halogen_df["Isotopic Composition"].astype(
        float
    )

    # Sort for consistent labeling
    halogen_df.sort_values(
        by=["Elemental Symbol", "Relative Atomic Mass"], inplace=True
    )

    # Add Isotope_Label (M, M+2, M+4, etc.)
    halogen_df["Isotope_Label"] = None
    for element in ["Br", "Cl"]:
        group = halogen_df[halogen_df["Elemental Symbol"] == element]
        for i, idx in enumerate(group.index):
            halogen_df.at[idx, "Isotope_Label"] = f"M+{i * 2}" if i > 0 else "M"

    # Normalize intensities per element group
    halogen_df["Normalized_Intensity"] = halogen_df.groupby("Elemental Symbol")[
        "Isotopic Composition"
    ].transform(lambda x: x / x.max())

    return halogen_df


def compute_isotopic_distribution(element_df, element_symbol="Cl", count=2):
    """
    Computes the normalized isotopic distribution for a given element and atom count using convolution.
    """
    filtered = element_df[element_df["Elemental Symbol"] == element_symbol].copy()

    if filtered.empty:
        raise ValueError(f"No isotopic data found for element: {element_symbol}")

    # Fix: convert Isotope_Label to Isotope_Order as integer
    filtered["Isotope_Order"] = (
        filtered["Isotope_Label"].str.replace("M", "0").str.replace("+", "").astype(int)
    )

    filtered = filtered.sort_values("Isotope_Order")
    intensities = filtered["Normalized_Intensity"].values

    distribution = intensities.copy()
    for _ in range(count - 1):
        distribution = np.convolve(distribution, intensities)

    distribution /= distribution.max()
    labels = [f"M+{i * 2}" for i in range(len(distribution))]

    return pd.DataFrame(
        {
            "Isotope_Label": labels,
            "Normalized_Intensity": distribution,
            "Combination": f"{element_symbol}{count}",
        }
    )


def compute_mixed_isotopic_distribution(halogen_df, max_atoms=3):
    """
    Computes isotopic distributions for all combinations of 1–3 Cl and 1–3 Br atoms,
    inserting zeroes at odd-numbered M+1, M+3, etc., to keep uniform labeling.
    """
    results = []

    for cl_count in range(0, max_atoms + 1):
        for br_count in range(0, max_atoms + 1):
            if cl_count == 0 and br_count == 0:
                continue

            cl_dist = (
                compute_isotopic_distribution(halogen_df, "Cl", cl_count)
                if cl_count > 0
                else pd.DataFrame({"Normalized_Intensity": [1.0]})
            )
            br_dist = (
                compute_isotopic_distribution(halogen_df, "Br", br_count)
                if br_count > 0
                else pd.DataFrame({"Normalized_Intensity": [1.0]})
            )

            # Perform convolution
            combined = np.convolve(
                cl_dist["Normalized_Intensity"], br_dist["Normalized_Intensity"]
            )
            combined /= combined.max()  # Normalize to max = 1

            # Insert 0s into odd M+ positions (i.e., M+1, M+3, etc.)
            extended = []
            for i in range(len(combined) * 2 - 1):
                if i % 2 == 0:
                    extended.append(combined[i // 2])
                else:
                    extended.append(0.0)

            labels = [f"M+{i}" for i in range(len(extended))]
            combination = f"Cl{cl_count}_Br{br_count}"

            df = pd.DataFrame(
                {
                    "Isotope_Label": labels,
                    "Normalized_Intensity": extended,
                    "Combination": combination,
                }
            )

            results.append(df)

    return pd.concat(results, ignore_index=True)


def merging_kaufman_df_with_isotopic_modeling(kaufman_df, multi_peak_df):
    """
    Adds the Predicted_F_per_C value from kaufman_df into multi_peak_df
    by matching on SampleName and Compound. Leaves all other columns in
    multi_peak_df unchanged.

    Parameters:
        kaufman_df (pd.DataFrame): Must contain ['Sample', 'Compound', 'Predicted_F_per_C']
        multi_peak_df (pd.DataFrame): Must contain ['SampleName', 'Compound']

    Returns:
        pd.DataFrame: Updated multi_peak_df with added Predicted_F_per_C column
    """
    # Create a lookup table from kaufman_df
    lookup = kaufman_df.set_index(["Sample", "Compound"])["Predicted_F_per_C"]

    # Map the predicted F/C value into multi_peak_df using SampleName as the key
    multi_peak_df = multi_peak_df.copy()
    multi_peak_df["Predicted_F_per_C"] = multi_peak_df.apply(
        lambda row: lookup.get((row["SampleName"], row["Compound"]), pd.NA), axis=1
    )

    return multi_peak_df


def heavy_halogen_isotopic_matching(labeled_df, theoretical_df, tolerance=0.1):
    """
    Match experimental isotopic patterns to theoretical ones based on Isotope_Label and Normalized_Intensity.
    Only checks Compound 74 in 'NIST SRM-1957 9.d.DeMP' for debugging.
    Returns a DataFrame with matched combination summaries.
    """
    if labeled_df is None or theoretical_df is None:
        raise ValueError("Input DataFrames cannot be None.")

    print("\n[DEBUG] Filtering labeled_df for Compound 74 in NIST SRM-1957 9.d.DeMP...")
    filtered_df = labeled_df
    if filtered_df.empty:
        print(
            "[WARNING] No entries found for Compound 74 in sample NIST SRM-1957 9.d.DeMP"
        )
        return pd.DataFrame()
    # Clean labels
    labeled_df["Isotope_Label"] = (
        labeled_df["Isotope_Label"].str.strip().replace("M", "M+0")
    )
    theoretical_df["Isotope_Label"] = (
        theoretical_df["Isotope_Label"].str.strip().replace("M", "M+0")
    )

    summary_rows = []

    for combination, ref_group in theoretical_df.groupby("Combination"):
        ref_group = ref_group.copy()
        ref_group["Isotope_Label"] = ref_group["Isotope_Label"].replace("M", "M+0")

        merged = pd.merge(
            filtered_df,
            ref_group,
            how="inner",
            on="Isotope_Label",
            suffixes=("_exp", "_ref"),
        )
        print("merged", merged)
        if merged.empty:
            print(f"[DEBUG] No matching isotope labels found for {combination}")
            continue

        merged["Isotope_Order"] = (
            merged["Isotope_Label"]
            .str.extract(r"M\+(\d+)", expand=False)
            .fillna("0")
            .astype(int)
        )
        merged["Intensity_Diff"] = (
            merged["Normalized_Intensity_exp"] - merged["Normalized_Intensity_ref"]
        ).abs()

        avg_diff = merged["Intensity_Diff"].mean()

        if avg_diff <= tolerance:
            print(f"\n[MATCH FOUND] {combination}")
            print(
                merged[
                    [
                        "Isotope_Label",
                        "Normalized_Intensity_exp",
                        "Normalized_Intensity_ref",
                        "Intensity_Diff",
                    ]
                ]
            )
            for _, row in merged.iterrows():
                summary_rows.append(
                    {
                        "SampleName": row["SampleName"],
                        "Compound": row["Compound"],
                        "Combination": combination,
                        "Isotope_Label": row["Isotope_Label"],
                        "Normalized_Intensity_exp": row["Normalized_Intensity_exp"],
                        "Normalized_Intensity_ref": row["Normalized_Intensity_ref"],
                        "Intensity_Diff": row["Intensity_Diff"],
                        "Avg_Diff": avg_diff,
                    }
                )

    if not summary_rows:
        print("\n[INFO] No isotopic matches found within tolerance.")
        return pd.DataFrame()

    return pd.DataFrame(summary_rows)


def add_predicted_f_to_matches(matches_df, kaufman_df):
    """
    Merge Predicted_F_per_C from kaufman_df into matches_df based on SampleName and Compound.

    Parameters:
        matches_df (pd.DataFrame): Output from heavy_halogen_isotopic_matching
        kaufman_df (pd.DataFrame): Contains Predicted_F_per_C, Sample, Compound

    Returns:
        pd.DataFrame: matches_df with added Predicted_F_per_C column
    """
    if matches_df.empty:
        print("[INFO] matches_df is empty, skipping merge.")
        return matches_df

    # Rename 'Sample' in kaufman_df to 'SampleName' to align with matches_df
    kaufman_df_renamed = kaufman_df.rename(columns={"Sample": "SampleName"})
    merged_df = pd.merge(
        matches_df,
        kaufman_df_renamed[
            ["SampleName", "Compound", "Predicted_F_per_C", "Peak_mz_1"]
        ],
        on=["SampleName", "Compound"],
        how="left",
    )

    return merged_df


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    file_path = r"PIMMS v1.2\CEF_reading\data\Isotopic modelling values (NIST).txt"
    csv_path = r"PIMMS v1.2\CEF_reading\data\Atomic numbers for elements.csv"
    kaufman_df = compute_kaufman_constants(multi_peak_df)
    kaufman_df = compute_mCm_alignment(kaufman_df)
    kaufman_df = compute_MDCm_alignment(kaufman_df)
    kaufman_df = cf2_prioritization(kaufman_df)
    kaufman_df = FC_prediction(kaufman_df)
    data = read_isotope_data(file_path)
    isotope_data = parse_isotope_data(data)
    isotope_data = add_elemental_symbol(isotope_data, csv_path)

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    multi_peak_df = merging_kaufman_df_with_isotopic_modeling(kaufman_df, multi_peak_df)
    labeled_df = label_isotopic_peaks(multi_peak_df)
    labeled_df = normalize_isotopic_intensity(labeled_df)
    halogen_isotopes = heavy_halogen_reader(isotope_data)
    theoretical_df = compute_mixed_isotopic_distribution(halogen_isotopes)
    matches = heavy_halogen_isotopic_matching(labeled_df, theoretical_df, tolerance=0.1)
    matches = add_predicted_f_to_matches(matches, kaufman_df)
    print(matches.head())


if __name__ == "__main__":
    main()
