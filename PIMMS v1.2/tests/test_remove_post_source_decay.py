import sys
import os
import pytest
import pandas as pd

# Add the module path manually
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
)

# Now, import the function
from post_source_decay_filter import remove_post_source_decay


def test_remove_post_source_decay():
    """Test that remove_post_source_decay correctly eliminates high CCS decay candidates."""

    # Input dataset
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.066, 3.066],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 176.79, 175.79, 185.79, 185.79],
            "m/z": [100, 100.00012, 200, 100, 100],
            "Classification Type": [
                "likely",
                "tentative",
                "likely",
                "unmatched",
                "tentative",
            ],
            "148 B2 16632.d.DeMP": [0, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [1, 20, 10, 10, 10],
        }
    )

    # Expected remaining IDs after filtering
    expected_remaining_ids = {1, 2, 3}

    # Run the filtering function
    adjusted_df = remove_post_source_decay(adjusted_df)

    # Extract remaining IDs
    remaining_ids = set(adjusted_df["ID"])

    # Assert that the expected IDs match the actual output
    assert remaining_ids == expected_remaining_ids, (
        f"Expected {expected_remaining_ids}, but got {remaining_ids}"
    )


if __name__ == "__main__":
    pytest.main()
