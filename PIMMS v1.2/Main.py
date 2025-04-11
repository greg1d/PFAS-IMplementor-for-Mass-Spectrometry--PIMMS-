import os
import sys

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (  # type: ignore
    count_non_zero_rows,
    process_standards_report_only,
    remove_standards_library,
)
from blank_subtraction_workflow import (  # type: ignore
    perform_blank_subtraction,
    process_files,
)
from branching_filter import (  # type: ignore
    branching_analyze,
    branching_merge,
)
from crude_filters import (  # type: ignore
    apply_mass_filter,
    apply_min_intensity_filter,
    apply_rt_filter,
)
from detection_frequency_filter import detection_frequency_filter  # type: ignore
from mass_defect_filter import (  # type: ignore
    mass_defect_filter,
)  # Importing the mass defect filter module
from ML_algorithm_density import (  # type: ignore
    fluorinated_density_filter,  # Importing fluorinated density filter
)
from monoisotopic_grouper import (  # type: ignore
    analyze_adjusted_df as mono_analyze,
)
from monoisotopic_grouper import (  # type: ignore
    merge_groups_into_adjusted_df as mono_merge,
)
from post_source_decay_filter import remove_post_source_decay
from regression_analysis import produce_filtered_df
from smearing_filter import (
    smearing_filter,  # type: ignore # Importing the smearing filter module
)
from Standard_library_scoring import (  # Import PFAS and External Library matching functions
    load_external_targets_library,
    load_pfas_library,
    match_external_targets,
    match_pfas_library,
)


def main():
    # File paths
    file_paths = [
        "PIMMS Validation work/PIMMS data/All Features - No Blank Subtraction.csv"
    ]
    standards_file = (
        "PIMMS v1.2/import folder/MPFAC HIF ES SIL peaks.csv"  # Standards library
    )
    standards_library_file = (
        "PIMMS Validation work/Target lists/Target_list_native_analytes.csv"
    )
    external_targets_file = (
        "PIMMS v1.2/import folder/Kauffman_M-H_external_PFAS_library_mz_only.csv"
    )

    # Define control columns
    control_samples = [f"Blank {i}.d" for i in range(1, 6)]

    # Set tolerances
    mass_error_ppm = 15  # Mass error in ppm
    ccs_error_percentage = 2  # CCS variance as 2% tolerance
    rt_tolerance = 0.5
    include_rt = False

    # Hardcoded filter parameters
    min_intensity = 10  # Minimum intensity cutoff
    rt_min = 2  # Minimum RT
    rt_max = 16  # Maximum RT
    mass_min = 68.98  # Minimum mass
    mass_max = 1700  # Maximum mass

    lower_mass_filter_bound = -0.11
    upper_mass_filter_bound = 0.12

    frequency_threshold = 30  # Detection frequency threshold percentage

    rt_filter = True
    ccs_filter = True

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
        # Save the adjusted dataframe after blank subtraction to a new CSV file
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_blank_subtraction.csv",
            index=False,
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
            # Save the adjusted dataframe after blank subtraction to a new CSV file

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
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_smearing_filter.csv",
            index=False,
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
        adjusted_df = branching_merge(groups)
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_branching_filter.csv", index=False
        )
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
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_monoisotopic_filter.csv",
            index=False,
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
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_fluorinated_density_filter.csv",
            index=False,
        )
    except Exception as e:
        print(f"[ERROR] Fluorinated density filter logic failed: {e}")
        sys.exit(1)

    print("[INFO] Applying mass defect filter...")
    try:
        adjusted_df = mass_defect_filter(
            adjusted_df, lower_mass_filter_bound, upper_mass_filter_bound
        )
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_mass_defect_filter.csv", index=False
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
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_detection_frequency_filter.csv",
            index=False,
        )

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
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_standards_removal.csv", index=False
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

    print("[INFO] Matching features against PFAS Standards Library...")
    pfas_library = load_pfas_library(standards_library_file)
    likely_matched_df, likely_unmatched_df = match_pfas_library(
        adjusted_df,
        pfas_library,
        standards_library_file,
        standards_library_file,
        mass_error_ppm,
        ccs_error_percentage,
        rt_tolerance,
        include_rt,
    )

    # **Step 2: Match Remaining Features Against External Targets Library**
    print("[INFO] Matching remaining features against External Targets Library...")
    external_targets_library = load_external_targets_library(external_targets_file)
    external_matched_df, external_unmatched_df = match_external_targets(
        likely_unmatched_df, external_targets_library, mass_error_ppm
    )

    # **Combine All Matches into Adjusted Dataset**
    adjusted_df = pd.concat(
        [likely_matched_df, external_matched_df, external_unmatched_df],
        ignore_index=True,
    )

    print("[INFO] Applying post filter decay filter...")
    try:
        adjusted_df = remove_post_source_decay(adjusted_df)
        adjusted_df.to_csv("PIMMS Validation work/PIMMS data/after_decay_filter 2.csv")

        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying post filter decay filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to perform mass defect filtering: {e}")
        sys.exit(1)

    print("[INFO] Applying regression analysis filter...")
    try:
        library_file = (
            r"PIMMS v1.2\CCSRT v mz predictions\Library Data for model building.csv"
        )
        adjusted_df = produce_filtered_df(
            adjusted_df,
            library_file,
            rt_filter,
            ccs_filter,
        )
        adjusted_df.to_csv(
            "PIMMS Validation work/PIMMS data/after_rt_CCS_filter.csv",
            index=False,
        )
        group_avg, group_std = count_non_zero_rows(adjusted_df)
        print(
            f"[INFO] After Applying post filter decay filter:\n"
            f"  Average Non-Zero Rows: {group_avg}\n"
            f"  Std Dev of Non-Zero Rows: {group_std}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to perform regression analysis: {e}")
        sys.exit(1)

    output_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    adjusted_df.to_csv(output_path, index=False)
    print(f"[INFO] Final adjusted dataset saved to {output_path}")
    print(adjusted_df.head())


if __name__ == "__main__":
    main()
