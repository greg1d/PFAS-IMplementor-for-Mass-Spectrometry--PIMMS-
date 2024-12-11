"""
# Citations

- [DOI: 10.1351/PAC-REP-10-06-02](https://doi.org/10.1351/PAC-REP-10-06-02)
- J. S. Coursey, D. J. Schwab, J. J. Tsai, and R. A. Dragoset
- NIST Physical Measurement Laboratory
- [IOP Science Article](https://iopscience.iop.org/article/10.1088/1674-1137/36/12/003)
- [CIAAW Atomic Weights](https://www.ciaaw.org/atomic-weights.htm)
"""

import os
import re

import pandas as pd


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
    print("Parsed Data Dictionary:")
    for key, values in data_dict.items():
        print(f"{key}: {values}")

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

    # Debug: Print rows with None in Atomic Number column
    print("Rows with None in Atomic Number column:")
    print(df[df["Atomic Number"].isna()])

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

    # Print the entire dataset
    print(df.to_string())

    return df


# Example usage
current_dir = os.path.dirname(__file__)
file_path = r"data/Isotopic modelling values (NIST).txt"
csv_path = r"data/Atomic numbers for elements.csv"

data = read_isotope_data(file_path)
isotope_data = parse_isotope_data(data)
isotope_data = add_elemental_symbol(isotope_data, csv_path)
