import os
import sys

# Add the 'modules/' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../modules")))

from CCS_mz_trend_analysis import CCS_vs_mz_trend_analysis


def test_CCS_vs_mz_trend_analysis():
    # Path to the existing testing CSV file
    file_path = os.path.join(os.path.dirname(__file__), "Dummy scored data.csv")

    # Define input groups (m/z values from the CSV)
    groups = [[298.9416, 348.9383, 398.9367, 448.9341]]
    variation_threshold = 0.02  # Allowable variation for inclusion

    # Call the function
    homologous_series_groups = CCS_vs_mz_trend_analysis(
        file_path, groups, variation_threshold
    )

    # Expected result: All points should be grouped together
    expected_group = [
        {"m/z": 298.9416, "CCS": 133.6, "Score": "A"},
        {"m/z": 348.9383, "CCS": 142.15, "Score": "A"},
        {"m/z": 398.9367, "CCS": 150.91, "Score": "C"},
        {"m/z": 448.9341, "CCS": 158.76, "Score": "A"},
    ]

    # Validate that an additional point is excluded
    excluded_point = [
        {"m/z": 398.9367, "CCS": 170.0, "Score": "A"},
    ]

    # Debugging: Print returned and expected groups
    print(f"Returned group: {homologous_series_groups[0]}")
    print(f"Expected group: {expected_group}")

    # Assertions
    assert len(homologous_series_groups) == 1, (
        "Should return one homologous series group"
    )
    assert sorted(homologous_series_groups[0], key=lambda x: x["m/z"]) == sorted(
        expected_group, key=lambda x: x["m/z"]
    ), f"Expected {expected_group}, but got {homologous_series_groups[0]}"

    # Ensure the excluded point is not in the group
    assert excluded_point not in homologous_series_groups[0], (
        f"Point {excluded_point} should not be included in the group"
    )
