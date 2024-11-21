import os
import sys
import pandas as pd
import pytest

# Add the parent directory to the sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(parent_dir)

from Isotopic_modeling.data.Atomic_weight_importing import (
    read_isotope_data,
    parse_isotope_data,
    add_elemental_symbol,
)


def test_atomic_weight_importing():
    # Define the paths
    file_path = os.path.join(
        current_dir, "../../Isotopic_modeling/data/Isotopic modelling values (NIST).txt"
    )
    csv_path = os.path.join(
        current_dir, "../../Isotopic_modeling/data/Atomic numbers for elements.csv"
    )

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

    # Print the relevant rows for Atomic Number 80
    print("Relevant rows for Atomic Number 80:")
    print(relevant_rows.to_string())


if __name__ == "__main__":
    pytest.main()
