"""
# Citations

Coursey, J. S.; Schwab, D. J.; Tsai, J. J.; Dragoset, R. A. Pure Appl. Chem. 2011, 83, 359. https://doi.org/10.1351/PAC-REP-10-06-02.

Coursey, J. S.; Schwab, D. J.; Tsai, J. J.; Dragoset, R. A. NIST Physical Measurement Laboratory, 2010. https://www.nist.gov/pml/atomic-weights-and-isotopic-compositions-relative-atomic-masses.

Qian, Y.; He, Z.; Wu, Q. Chin. Phys. C 2012, 36, 1141. https://doi.org/10.1088/1674-1137/36/12/003.

CIAAW. IUPAC Commission on Isotopic Abundances and Atomic Weights. https://www.ciaaw.org/atomic-weights.htm.
"""

import os
import pandas as pd
import re


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
        "Notes": re.compile(r"Notes = (\w+)"),
    }

    # Initialize lists to store the parsed data
    data_dict = {key: [] for key in patterns.keys()}

    # Split the data into lines
    lines = data.split("\n")

    # Process the lines in chunks corresponding to each data point
    chunk_size = 7  # Each data point is composed of 7 lines
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]
        for key, pattern in patterns.items():
            for line in chunk:
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

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data_dict)

    # Exclude rows with empty Isotopic Composition
    df = df[df["Isotopic Composition"].notna()]

    # Drop the Notes column
    df = df.drop(columns=["Notes"])

    return df


# Example usage
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "Test for import.txt")
data = read_isotope_data(file_path)
isotope_data = parse_isotope_data(data)

# Print all data
print(isotope_data.to_string())
