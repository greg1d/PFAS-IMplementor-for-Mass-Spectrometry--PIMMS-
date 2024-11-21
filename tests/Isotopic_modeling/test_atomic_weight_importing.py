import os
import sys
import pytest

# Add the directory containing the script to the sys.path
current_dir = os.path.dirname(__file__)
script_dir = os.path.abspath(os.path.join(current_dir, "../../Isotopic_modeling/data"))
sys.path.append(script_dir)

# Debug: Print the sys.path and script_dir
print("sys.path:")
for path in sys.path:
    print(path)
print(f"script_dir: {script_dir}")

from Atomic_weight_importing import (
    read_isotope_data,
    parse_isotope_data,
    add_elemental_symbol,
)


def test_atomic_number_55():
    # Define the paths
    file_path = os.path.join(script_dir, "Isotopic modelling values (NIST).txt")
    csv_path = os.path.join(script_dir, "Atomic numbers for elements.csv")

    # Read and parse the data
    data = read_isotope_data(file_path)
    isotope_data = parse_isotope_data(data)
    isotope_data = add_elemental_symbol(isotope_data, csv_path)

    # Check if the relevant rows for Atomic Number 55 are present
    relevant_rows = isotope_data[isotope_data["Atomic Number"] == 55]
    assert not relevant_rows.empty, "No relevant rows found for Atomic Number 55"

    # Check if the Elemental Symbol for Atomic Number 55 is Cs
    assert (
        relevant_rows["Elemental Symbol"].iloc[0] == "Cs"
    ), "Elemental Symbol for Atomic Number 55 is not Cs"

    # Print the relevant rows for Atomic Number 55
    print("Relevant rows for Atomic Number 55:")
    print(relevant_rows.to_string())


if __name__ == "__main__":
    pytest.main()
