import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import remove_standards_library, save_adjusted_dataset
from blank_subtraction_workflow import (
    perform_blank_subtraction,
    process_files,
)


def main():
    # File paths to the CSV files
    file_paths = [
        "PIMMS v1.2/data/debugging_data_set.csv",
    ]
    standards_file = "PIMMS v1.2/data/standards_library.csv"  # Standards library file

    # Define control columns
    control_samples = [
        "Blank 1.d",
        "Blank 2.d",
        "Blank 3.d",
    ]

    try:
        # Process files and separate data
        combined_data, control_df, experimental_df = process_files(
            file_paths, control_samples
        )
    except Exception as e:
        print(f"Error processing files: {e}")
        sys.exit(1)

    # Remove standards library
    print("Remove standards library from experimental dataset? (Y/N)")
    choice = input("Enter your choice: ").strip().upper()
    if choice == "Y":
        print("Processing standards library...")
        experimental_df, remaining_standards_df = remove_standards_library(
            control_df, experimental_df, standards_file
        )
    else:
        print("Proceeding without removing the standards library.")

    # Select the blank subtraction method
    print("Select blank subtraction method:")
    print("1: Method 1 (Highest signal from control samples)")
    print("2: Method 2 (Mean + x standard deviations)")
    method = input("Enter method number: ")

    try:
        # Perform blank subtraction
        adjusted_df, control_mean, control_std = perform_blank_subtraction(
            method, control_df, experimental_df
        )

        # Save the adjusted dataset, including the first 5 columns
        save_adjusted_dataset(adjusted_df, combined_data)

        # Save the remaining standards library
        if choice == "Y":
            remaining_standards_file = (
                "PIMMS v1.2/.temp/identified_features_matching_to_standards.csv"
            )
            remaining_standards_df.to_csv(remaining_standards_file, index=False)
            print(f"Remaining standards library saved to {remaining_standards_file}")

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
