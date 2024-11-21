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
        "Relative Atomic Mass": re.compile(r"Relative Atomic Mass = ([\d.()#]+)"),
        "Isotopic Composition": re.compile(r"Isotopic Composition = ([\d.()#]*)"),
        "Standard Atomic Weight": re.compile(r"Standard Atomic Weight = ([\d.,\[\]]+)"),
        "Notes": re.compile(r"Notes = (\w+)"),
    }

    # Initialize lists to store the parsed data
    data_dict = {key: [] for key in patterns.keys()}

    # Split the data into lines
    lines = data.split("\n")

    # Parse each line
    for line in lines:
        for key, pattern in patterns.items():
            match = pattern.search(line)
            if match:
                data_dict[key].append(match.group(1))

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data_dict)

    return df


# Example usage
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "Isotopic modelling values (NIST).txt")
print(file_path)
data = read_isotope_data(file_path)
isotope_data = parse_isotope_data(data)

# Print all data
print(isotope_data.to_string())
