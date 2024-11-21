import os
import sys
import pytest

# Add the directory containing the script to the sys.path
current_dir = os.path.dirname(__file__)
script_dir = os.path.abspath(os.path.join(current_dir, "../../Isotopic_modeling/data"))
sys.path.append(script_dir)


from Atomic_weight_importing import (
    read_isotope_data,
    parse_isotope_data,
    add_elemental_symbol,
)


def test_atomic_weight_importing():
    # Define the paths
    file_path = os.path.join(script_dir, "Isotopic modelling values (NIST).txt")
    csv_path = os.path.join(script_dir, "Atomic numbers for elements.csv")

    # Read and parse the data
    data = read_isotope_data(file_path)
    isotope_data = parse_isotope_data(data)
    isotope_data = add_elemental_symbol(isotope_data, csv_path)

    # Check if the DataFrame is not empty
    assert not isotope_data.empty, "The DataFrame is empty"

    # Check if the Elemental Symbol column is present
    assert (
        "Elemental Symbol" in isotope_data.columns
    ), "Elemental Symbol column is missing"

    # Check if the relevant rows for Atomic Number 80 are present
    relevant_rows = isotope_data[isotope_data["Atomic Number"] == 80]
    assert not relevant_rows.empty, "No relevant rows found for Atomic Number 80"


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


def test_isotopic_composition_o_16():
    # Define the paths
    file_path = os.path.join(script_dir, "Isotopic modelling values (NIST).txt")
    csv_path = os.path.join(script_dir, "Atomic numbers for elements.csv")

    # Read and parse the data
    data = read_isotope_data(file_path)
    isotope_data = parse_isotope_data(data)
    isotope_data = add_elemental_symbol(isotope_data, csv_path)

    # Print all rows for Elemental Symbol O
    o_rows = isotope_data[isotope_data["Elemental Symbol"] == "O"]
    print("All rows for Elemental Symbol O:")
    print(o_rows.to_string())

    # Check if the relevant rows for Elemental Symbol O and Mass Number 16 are present

    assert (
        not o_rows.empty
    ), "No relevant rows found for Elemental Symbol O with Mass Number 16"

    # Check if the Isotopic Composition for Elemental Symbol O with Mass Number 16 is 0.99757
    assert (
        o_rows["Isotopic Composition"].iloc[0] == "0.99757"
    ), "Isotopic Composition for Elemental Symbol O with Mass Number 16 is not 0.99757"

    # Print the relevant rows for Elemental Symbol O with Mass Number 16
    print("Relevant rows for Elemental Symbol O with Mass Number 16:")
    print(o_rows.to_string())


if __name__ == "__main__":
    pytest.main()
