import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
sys.path.append(os.path.join(os.path.dirname(__file__), "import folder"))
from blank_subtraction import read_and_filter_csv, blank_subtraction
from gui_module import launch_column_selection_gui


def main():
    # File paths to the CSV files
    file_paths = [
        "PIMMS v1.2/data/raw_data_test_set.csv",
        "PIMMS v1.2/data/another_test_set.csv",
    ]

    # Combine data from multiple files
    combined_data = pd.DataFrame()

    print("Reading and filtering data from multiple files...")
    for file_path in file_paths:
        try:
            filtered_data = read_and_filter_csv(file_path)
            combined_data = pd.concat([combined_data, filtered_data], ignore_index=True)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    # Check if any data was loaded
    if combined_data.empty:
        print("No valid data loaded from the files. Exiting.")
        sys.exit(1)

    # Launch GUI to select experimental, control, or exclude columns
    columns_to_select = combined_data.columns[5:].tolist()  # Exclude first 5 columns
    selections = launch_column_selection_gui(columns_to_select)

    # Extract user inputs
    control_columns = selections["control"]
    experimental_columns = selections["experimental"]
    std_deviation_factor = selections["std_deviation_factor"]

    if not control_columns or not experimental_columns:
        print("No control or experimental samples selected. Exiting.")
        sys.exit(1)

    # Extract the control and experimental samples
    control_df = combined_data[control_columns]
    experimental_df = combined_data[experimental_columns]

    # Perform blank subtraction
    try:
        subtracted_df, control_mean, control_std = blank_subtraction(
            control_df, experimental_df
        )

        # Apply the standard deviation factor to modify the blank subtraction
        adjusted_df = experimental_df.copy()
        for column in adjusted_df.columns:
            adjusted_df[column] -= std_deviation_factor * control_std
            adjusted_df[column] = adjusted_df[column].clip(
                lower=0
            )  # Ensure no negative values

        # Debugging: Display results
        print("\nAdjusted Experimental Data Preview:")
        print(adjusted_df.head())

        print("\nControl Row-Wise Means:")
        print(control_mean.head())

        print("\nControl Row-Wise Standard Deviations:")
        print(control_std.head())

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
