import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (
    process_standards_report_only,
    remove_standards_library,
    save_adjusted_dataset,
    count_non_zero_rows,
)
from blank_subtraction_workflow import (
    perform_blank_subtraction,
    process_files,
)
from crude_filters import apply_mass_filter, apply_min_intensity_filter, apply_rt_filter


def main():
    # File paths to the CSV files
    file_paths = [
        "PIMMS v1.2/data/20202021_data_set.csv",
    ]
    standards_file = (
        "PIMMS v1.2/import folder/MPFAC HIF ES SIL peaks.csv"  # Standards library file
    )

    # Define control columns
    control_samples = [
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

    # Set tolerances
    mass_error_ppm = 10  # Mass error in ppm
    ccs_error_percentage = 2  # CCS variance as 2% tolerance
    rt_tolerance = 0.5

    # Hardcoded filter parameters
    min_intensity = 500  # Minimum intensity cutoff
    rt_min = 0.5  # Minimum RT
    rt_max = 10.0  # Maximum RT
    mass_min = 50.0  # Minimum mass
    mass_max = 1500  # Maximum mass

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
        experimental_df = remove_standards_library(
            control_df, experimental_df, standards_file
        )
    elif choice == "N":
        print("Generating Standards Report without removing matched features...")
        process_standards_report_only(
            experimental_df,
            standards_file,
            mass_error_ppm=10,
            ccs_error_percentage=2,
            z=1,
        )
    else:
        print("Invalid choice. Proceeding without processing standards library.")

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

        # Apply filters
        print("[INFO] Applying filters to adjusted dataset...")
        try:
            adjusted_df = apply_min_intensity_filter(adjusted_df, min_intensity)
            adjusted_df = apply_rt_filter(adjusted_df, rt_min, rt_max)
            adjusted_df = apply_mass_filter(adjusted_df, mass_min, mass_max)
        except Exception as e:
            print(f"[ERROR] Filtering failed: {e}")
            sys.exit(1)

        # Count non-zero rows after filters
        print("[INFO] Calculating non-zero row statistics after filters...")
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] Summary After Filters:\n"
            f"  Average Non-Zero Rows: {group_avg:.2f}\n"
            f"  Std Dev of Non-Zero Rows: {group_std:.2f}"
        )

        # Save the adjusted dataset, including the first 5 columns
        save_adjusted_dataset(adjusted_df, combined_data)

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
