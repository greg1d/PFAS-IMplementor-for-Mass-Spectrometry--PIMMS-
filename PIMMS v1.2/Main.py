import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction_workflow import process_files, perform_blank_subtraction


def main():
    # File paths to the CSV files
    file_paths = [
        "PIMMS v1.2/data/raw_data_test_set.csv",
    ]

    # Define control columns
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

    try:
        # Process files and separate data
        combined_data, control_df, experimental_df = process_files(
            file_paths, control_columns
        )
    except Exception as e:
        print(f"Error processing files: {e}")
        sys.exit(1)

    # Select the blank subtraction method
    print("Select blank subtraction method:")
    print("1: Method 1")
    print("2: Method 2 (Mean + x standard deviations)")
    print("3: Method 3")
    method = input("Enter method number: ")

    try:
        # Perform blank subtraction
        adjusted_df, control_mean, control_std = perform_blank_subtraction(
            method, control_df, experimental_df
        )

        # Debugging: Display results
        print("\nAdjusted Experimental Data Preview:")
        print(adjusted_df.head())

        print("\nControl Row-Wise Means:")
        print(control_mean.head())

        if control_std is not None:
            print("\nControl Row-Wise Standard Deviations:")
            print(control_std.head())

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
