import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (
    method_1_blank_subtraction,
    method_2_blank_subtraction,
    method_3_blank_subtraction,
    read_and_filter_csv,
)


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

    # Separate control and experimental DataFrames
    control_columns = [
        "Blank 1.d",
        "Blank 2.d",
        "Blank 3.d",
        "Blank 4.d",
        "Blank 5.d",
        "Blank 6.d",
        "Blank 7.d",
        "Blank 8.d",
        "Blank 9.d",
    ]
    control_df = combined_data[["ID", "RT", "DT", "CCS", "m/z"] + control_columns]
    experimental_columns = [
        col
        for col in combined_data.columns
        if col not in control_columns and col not in ["ID", "RT", "DT", "CCS", "m/z"]
    ]
    experimental_df = combined_data[
        ["ID", "RT", "DT", "CCS", "m/z"] + experimental_columns
    ]

    # Choose a blank subtraction method
    print("\nChoose a blank subtraction method:")
    print("1. Method 1: Basic Subtraction")
    print("2. Method 2: Subtraction with Mean + Standard Deviation")
    print("3. Method 3: Custom Advanced Subtraction")

    try:
        choice = int(input("\nEnter your choice (1, 2, or 3): "))
    except ValueError:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    if choice == 1:
        print("\nPerforming Method 1: Basic Subtraction...")
        try:
            adjusted_df = method_1_blank_subtraction(control_df, experimental_df)
            print("\nAdjusted Experimental Data (Method 1):")
            print(adjusted_df.head())
        except Exception as e:
            print(f"Error during Method 1 blank subtraction: {e}")
    elif choice == 2:
        print("\nPerforming Method 2: Subtraction with Mean + Standard Deviation...")
        try:
            adjusted_df, control_mean, control_std = method_2_blank_subtraction(
                control_df, experimental_df, std_deviation_factor=3
            )
            print("\nAdjusted Experimental Data (Method 2):")
            print(adjusted_df.head())
        except Exception as e:
            print(f"Error during Method 2 blank subtraction: {e}")
    elif choice == 3:
        print("\nPerforming Method 3: Custom Advanced Subtraction...")
        try:
            adjusted_df = method_3_blank_subtraction(control_df, experimental_df)
            print("\nAdjusted Experimental Data (Method 3):")
            print(adjusted_df.head())
        except Exception as e:
            print(f"Error during Method 3 blank subtraction: {e}")
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
