from Modules.Monoisotopic_peak_puller import find_related_peaks_in_csv
from tqdm import tqdm
import time


def main():
    file_path = "data\Dummy test blank subtracted data.csv"  # Update this path to your local CSV file
    z_range = range(1, 5)  # This will check for z = 1 to 99
    M_range = range(1, 5)  # This will check for M = 1 to 5
    mass_error_ppm = 10  # Define the mass error in ppm

    # Start the progress bar
    with tqdm(total=100, desc="Processing peaks") as pbar:
        start_time = time.time()

        (
            related_peaks,
            iteration_count,
            comparisons,
            parent_child_baby_relationships,
            collapsed_features,
        ) = find_related_peaks_in_csv(file_path, z_range, M_range, mass_error_ppm)

        # Simulate progress update
        pbar.update(100)

        end_time = time.time()
        elapsed_time = end_time - start_time

    # Print the number of calculations
    print(f"Number of calculations: {iteration_count}")
    print("Summary of comparisons:")
    for comparison in comparisons:
        print(comparison)
    # Print the parent, child, and baby peaks
    collapsed_features_count = 0
    unique_parents = set()
    for relationship in parent_child_baby_relationships:
        if relationship[2] == "parent-child":
            print(f"Parent peak: {relationship[0]}, Child peak: {relationship[1]}")
            unique_parents.add(relationship[0])
        elif relationship[2] == "baby":
            print(f"Baby peak: {relationship[1]}")
        elif relationship[2] == "loner":
            print(
                f"Loner peak: {relationship[1]} (related to Parent peak: {relationship[0]})"
            )
            unique_parents.add(relationship[0])

    collapsed_features_count = len(unique_parents)

    # Print the number of collapsed features
    print(f"Number of collapsed features: {collapsed_features_count}")

    # Allow searching by collapsed feature
    collapsed_feature_keys = list(collapsed_features.keys())
    if len(collapsed_feature_keys) >= 1:
        second_collapsed_feature_key = collapsed_feature_keys[0]
        print(
            f"Peaks in the 2nd Collapsed Feature: {collapsed_features[second_collapsed_feature_key]}"
        )
    else:
        print("There are less than 2 collapsed features.")

    print(f"Script completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()
