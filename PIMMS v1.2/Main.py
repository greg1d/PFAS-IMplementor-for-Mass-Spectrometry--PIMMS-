import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (  # type: ignore
    count_non_zero_rows,
    process_standards_report_only,
    remove_standards_library,
)
from blank_subtraction_workflow import perform_blank_subtraction, process_files  # type: ignore
from branching_filter import (  # type: ignore
    analyze_adjusted_df as branching_analyze,
)
from branching_filter import (  # type: ignore
    merge_groups_into_adjusted_df as branching_merge,
)
from crude_filters import apply_mass_filter, apply_min_intensity_filter, apply_rt_filter  # type: ignore
from ML_algorithm_density import (  # type: ignore
    fluorinated_density_filter,  # Importing fluorinated density filter
)
from monoisotopic_grouper import (  # type: ignore
    analyze_adjusted_df as mono_analyze,
)
from monoisotopic_grouper import (  # type: ignore
    merge_groups_into_adjusted_df as mono_merge,
)
from smearing_filter import smearing_filter  # type: ignore # Importing the smearing filter module
from mass_defect_filter import (  # type: ignore
    mass_defect_filter,
)  # Importing the mass defect filter module
from detection_frequency_filter import detection_frequency_filter  # type: ignore


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
    rt_max = 5  # Maximum RT
    mass_min = 68.98  # Minimum mass
    mass_max = 1700  # Maximum mass

    lower_mass_filter_bound = -0.11
    upper_mass_filter_bound = 0.12

    frequency_threshold = 20  # Detection frequency threshold percentage

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
            adjusted_df = apply_rt_filter(adjusted_df, rt_min, rt_max)
            adjusted_df = apply_mass_filter(adjusted_df, mass_min, mass_max)

            group_avg, group_std = count_non_zero_rows(adjusted_df)
            print(
                f"[INFO] After Applying All Filters:\n"
                f"  Average Non-Zero Rows: {group_avg}\n"
                f"  Std Dev of Non-Zero Rows: {group_std}"
            )
        except Exception as e:
            print(f"[ERROR] Filtering failed: {e}")
            sys.exit(1)

    except Exception as e:
        print(f"Error during blank subtraction: {e}")
        sys.exit(1)

    # Step 3: Apply Smearing Filter
    print("[INFO] Applying smearing filter to remove mass shift artifacts...")
    try:
        adjusted_df = smearing_filter(
            adjusted_df,
            rt_tolerance=rt_tolerance,
            ccs_tolerance=ccs_error_percentage,
        )

        # Count non-zero rows after smearing filter
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying Smearing Filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )
    except Exception as e:
        print(f"[ERROR] Smearing filter logic failed: {e}")
        sys.exit(1)

    # Step 4: Apply Grouping Logic (Branching Filter)
    print("[INFO] Applying branching filter for grouping...")
    try:
        groups = branching_analyze(
            adjusted_df,
            mass_error_ppm=mass_error_ppm,
            rt_tolerance=rt_tolerance,
            ccs_tolerance=ccs_error_percentage,
        )
        print(f"[INFO] Number of groups identified by branching filter: {len(groups)}")

        # Merge groups into adjusted_df
        adjusted_df = branching_merge(adjusted_df, groups)

        # Count non-zero rows after merging
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying Branching Filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )

    except Exception as e:
        print(f"[ERROR] Branching filter logic failed: {e}")
        sys.exit(1)

    # Step 5: Apply Monoisotopic Filter
    print("[INFO] Applying monoisotopic filter for grouping...")
    try:
        groups = mono_analyze(
            adjusted_df,
            z_range=range(1, 4),
            mass_error_ppm=mass_error_ppm,
            rt_tolerance=rt_tolerance,
            ccs_tolerance=ccs_error_percentage,
        )
        print(
            f"[INFO] Number of groups identified by monoisotopic filter: {len(groups)}"
        )

        # Merge groups into adjusted_df
        adjusted_df = mono_merge(adjusted_df, groups)

        # Count non-zero rows after merging
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying Monoisotopic Filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )

    except Exception as e:
        print(f"[ERROR] Monoisotopic filter logic failed: {e}")
        sys.exit(1)

    print("[INFO] Applying fluorinated density filter...")
    try:
        adjusted_df = fluorinated_density_filter(adjusted_df)
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying Fluorinated Density Filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )
    except Exception as e:
        print(f"[ERROR] Fluorinated density filter logic failed: {e}")
        sys.exit(1)

    print("[INFO] Applying mass defect filter...")
    try:
        adjusted_df = mass_defect_filter(
            adjusted_df, lower_mass_filter_bound, upper_mass_filter_bound
        )
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After performing mass defect analysis:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to perform mass defect filtering: {e}")
        sys.exit(1)

    # Step 7: Detection Frequency Cutoff
    print("[INFO] Performing detection frequency cutoff...")
    try:
        adjusted_df = detection_frequency_filter(adjusted_df, frequency_threshold)

        # Count non-zero rows after removing standards
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After performing detection frequency cutoff:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )

    except Exception as e:
        print(f"[ERROR] Failed to perform detection frequency cutoff: {e}")
        sys.exit(1)

    # Step 8: Remove Standards as Final Step
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

    except Exception as e:
        print(f"[ERROR] Failed to remove standards: {e}")
        sys.exit(1)

    output_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    adjusted_df.to_csv(output_path, index=False)
    print(f"[INFO] Final adjusted dataset saved to {output_path}")


if __name__ == "__main__":
    main()
