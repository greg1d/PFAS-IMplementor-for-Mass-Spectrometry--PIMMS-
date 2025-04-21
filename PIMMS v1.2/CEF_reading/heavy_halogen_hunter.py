from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
import re
import time


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


def heavy_halogen_hunter(isotope_df):
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


def main():
    start_all = time.time()

    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    file_path = r"PIMMS v1.2\CEF_reading\data\Isotopic modelling values (NIST).txt"
    csv_path = r"PIMMS v1.2\CEF_reading\data\Atomic numbers for elements.csv"

    t0 = time.time()
    data = read_isotope_data(file_path)
    print(f"[TIMER] Reading isotope data: {time.time() - t0:.2f} s")

    t1 = time.time()
    isotope_data = parse_isotope_data(data)
    print(f"[TIMER] Parsing isotope data: {time.time() - t1:.2f} s")

    t2 = time.time()
    isotope_data = add_elemental_symbol(isotope_data, csv_path)
    print(f"[TIMER] Adding elemental symbols: {time.time() - t2:.2f} s")

    t3 = time.time()
    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    print(f"[TIMER] match_PIMMS_to_CEF: {time.time() - t3:.2f} s")

    t4 = time.time()
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    print(f"[TIMER] show_multi_peak_compound_matches: {time.time() - t4:.2f} s")

    if multi_peak_df.empty:
        print("[INFO] No multi-peak compound matches to compute Kaufman constants.")
        return pd.DataFrame()

    t5 = time.time()
    labeled_df = label_isotopic_peaks(multi_peak_df)
    print(f"[TIMER] Labeling isotopic peaks: {time.time() - t5:.2f} s")

    t6 = time.time()
    labeled_df = normalize_isotopic_intensity(labeled_df)
    print(f"[TIMER] Normalizing isotopic intensities: {time.time() - t6:.2f} s")

    t7 = time.time()
    halogen_isotopes = heavy_halogen_hunter(isotope_data)
    print(f"[TIMER] Identifying Br/Cl isotopes: {time.time() - t7:.2f} s")

    print("\n[INFO] === Final labeled DataFrame Preview ===")
    print(labeled_df.head())
    print("\n[INFO] === Halogen Reference Isotopes ===")
    print(halogen_isotopes)

    print(f"\n[TOTAL TIME] Script completed in {time.time() - start_all:.2f} seconds.")


if __name__ == "__main__":
    main()
