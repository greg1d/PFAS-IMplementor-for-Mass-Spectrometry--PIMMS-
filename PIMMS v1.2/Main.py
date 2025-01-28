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
    min_intensity = 100  # Minimum intensity cutoff
    rt_min = 0.5  # Minimum RT
    rt_max = 10.0  # Maximum RT
    mass_min = 50.0  # Minimum mass
    mass_max = 1500.0  # Maximum mass

    try:
        # Process files and separate data
        combined_data, control_df, experimental_df = process_files(
            file_paths, control_samples
        )
    except Exception as e:
        print(f"Error processing files: {e}")
        sys.exit(1)

    # Count non-zero rows in the raw experimental dataset
    group_avg, group_std = count_non_zero_rows(experimental_df)
    print(
        f"[INFO] Raw Experimental Data:\n"
        f"  Average Non-Zero Rows: {group_avg}\n"
        f"  Std Dev of Non-Zero Rows: {group_std}"
    )

    # Step 1: Generate Standards Report (No removal of features yet)
    print("[INFO] Generating Standards Report without removing matched features...")
    try:
        process_standards_report_only(
            experimental_df,
            standards_file,
            mass_error_ppm=mass_error_ppm,
            ccs_error_percentage=ccs_error_percentage,
            z=1,
        )
    except Exception as e:
        print(f"[ERROR] Failed to generate Standards Report: {e}")
        sys.exit(1)

    # Step 2: Perform Blank Subtraction and Filtering
    print("Select blank subtraction method:")
    print("1: Method 1 (Highest signal from control samples)")
    print("2: Method 2 (Mean + x standard deviations)")
    method = input("Enter method number: ")

    try:
        # Perform blank subtraction
        adjusted_df, control_mean, control_std = perform_blank_subtraction(
            method, control_df, experimental_df
        )

        # Count non-zero rows after blank subtraction
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Blank Subtraction:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )

        # Apply filters
        print("[INFO] Applying filters to adjusted dataset...")
        try:
            adjusted_df = apply_min_intensity_filter(adjusted_df, min_intensity)
            group_avg, group_std = count_non_zero_rows(adjusted_df)
            print(
                f"[INFO] After Intensity Filter:\n"
                f"  Average Non-Zero Rows: {group_avg}\n"
                f"  Std Dev of Non-Zero Rows: {group_std}"
            )

            adjusted_df = apply_rt_filter(adjusted_df, rt_min, rt_max)
            group_avg, group_std = count_non_zero_rows(adjusted_df)
            print(
                f"[INFO] After RT Filter:\n"
                f"  Average Non-Zero Rows: {group_avg}\n"
                f"  Std Dev of Non-Zero Rows: {group_std}"
            )

            adjusted_df = apply_mass_filter(adjusted_df, mass_min, mass_max)
            group_avg, group_std = count_non_zero_rows(adjusted_df)
            print(
                f"[INFO] After Mass Filter:\n"
                f"  Average Non-Zero Rows: {group_avg}\n"
                f"  Std Dev of Non-Zero Rows: {group_std}"
            )
        except Exception as e:
            print(f"[ERROR] Filtering failed: {e}")
            sys.exit(1)

        # Save the adjusted dataset, including the first 5 columns
        save_adjusted_dataset(adjusted_df, combined_data)

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)

    # Step 3: Remove Standards as Final Step
    print("[INFO] Removing matched features from adjusted dataset...")
    try:
        adjusted_df = remove_standards_library(
            adjusted_df,
            standards_file,
            mass_error_ppm=mass_error_ppm,
            ccs_error_percentage=ccs_error_percentage,
            z=1,
        )

        # Count non-zero rows after removing standards
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Removing Standards:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )

        # Save the final dataset after standards removal
        final_csv_path = "PIMMS v1.2/.temp/final_adjusted_df.csv"
        os.makedirs(os.path.dirname(final_csv_path), exist_ok=True)
        adjusted_df.to_csv(final_csv_path, index=False)
        print(f"[INFO] Final adjusted dataset saved to {final_csv_path}")

    except Exception as e:
        print(f"[ERROR] Failed to remove standards: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
