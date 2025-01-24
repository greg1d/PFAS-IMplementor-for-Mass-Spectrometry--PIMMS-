import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (
    method_1_blank_subtraction,
    method_2_blank_subtraction,
    method_3_blank_subtraction,
    read_and_filter_csv,
    separate_control_experimental,
)


def main():
    # File paths to the CSV files
    file_paths = [
        "PIMMS v1.2/data/raw_data_test_set.csv",
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

    # Separate control and experimental data
    try:
        control_df, experimental_df = separate_control_experimental(
            combined_data,
            control_columns=[
                "Blank 1.d",
                "Blank 2.d",
                "Blank 3.d",
                "Blank 4.d",
                "Blank 5.d",
                "Blank 6.d",
                "Blank 7.d",
                "Blank 8.d",
                "Blank 9.d",
            ],
        )
    except Exception as e:
        print(f"Error separating control and experimental data: {e}")
        sys.exit(1)

    # Select the blank subtraction method
    print("Select blank subtraction method:")
    print("1: Method 1")
    print("2: Method 2 (Mean + x standard deviations)")
    print("3: Method 3")
    method = input("Enter method number: ")

    if method == "1":
        # Perform Method 1
        try:
            adjusted_df, control_mean, control_std = method_1_blank_subtraction(
                control_df, experimental_df
            )
            print("\nMethod 1: Adjusted Experimental Data Preview:")
            print(adjusted_df.head())
        except Exception as e:
            print(f"Error during Method 1 blank subtraction: {e}")

    elif method == "2":
        # Ask for the standard deviation factor
        try:
            std_deviation_factor = float(
                input("Enter the number of standard deviations for subtraction: ")
            )
            adjusted_df, control_mean, control_std = method_2_blank_subtraction(
                control_df, experimental_df, std_deviation_factor
            )
            print(
                f"\nMethod 2 (Mean + {std_deviation_factor} SD): Adjusted Data Preview:"
            )
            print(adjusted_df.head())
        except ValueError:
            print(
                "Invalid input. Please enter a numeric value for the standard deviations."
            )
        except Exception as e:
            print(f"Error during Method 2 blank subtraction: {e}")

    elif method == "3":
        # Perform Method 3
        try:
            adjusted_df, control_mean, control_std = method_3_blank_subtraction(
                control_df, experimental_df
            )
            print("\nMethod 3: Adjusted Experimental Data Preview:")
            print(adjusted_df.head())
        except Exception as e:
            print(f"Error during Method 3 blank subtraction: {e}")

    else:
        print("Invalid method selected. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
