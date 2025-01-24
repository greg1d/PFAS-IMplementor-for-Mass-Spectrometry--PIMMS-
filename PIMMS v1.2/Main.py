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

    # Filter Control and Experimental samples based on selections
    control_columns = selections["control"]
    experimental_columns = selections["experimental"]

    if not control_columns or not experimental_columns:
        print("No control or experimental samples selected. Exiting.")
        sys.exit(1)

    # Extract the control and experimental samples
    control_df = combined_data[control_columns]
    experimental_df = combined_data[experimental_columns]

    # Debugging: Print columns for verification
    print("\nControl DataFrame Columns:")
    print(control_df.columns)
    print("\nExperimental DataFrame Columns:")
    print(experimental_df.columns)

    # Perform blank subtraction
    try:
        subtracted_df = blank_subtraction(control_df, experimental_df)
        print("\nSubtracted Data Preview:")
        print(subtracted_df.head())
    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
