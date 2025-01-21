import os
import sys

import pytest

# Add the path to the module you want to test
current_dir = os.path.dirname(__file__)
script_dir = os.path.abspath(os.path.join(current_dir, "../../Isotopic_modeling/data"))
sys.path.append(script_dir)

from Monoisotopic_peak_puller import calculate_mass_error


def test_calculate_mass_error():
    mass = 600
    mass_error_ppm = 10
    lower_bound, upper_bound = calculate_mass_error(mass, mass_error_ppm)
    assert (
        lower_bound == 599.994
    ), f"Expected lower bound to be 599.994 but got {lower_bound}"
    assert (
        upper_bound == 600.006
    ), f"Expected upper bound to be 600.006 but got {upper_bound}"


if __name__ == "__main__":
    pytest.main()
