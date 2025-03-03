import pandas as pd
from neutral_mass_loss_analysis import (
    neutral_loss_analysis,
    filter_neutral_loss_groups,
)


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}

    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )

    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss = filter_neutral_loss_groups(
        neutral_loss_groups, dt_threshold=0.1, rt_threshold=1, comparison_type="both"
    )
    print("[INFO] Filtered neutral loss groups:\n", filtered_neutral_loss)


if __name__ == "__main__":
    main()
