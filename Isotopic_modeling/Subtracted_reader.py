from Modules.binary_logic_puller import analyze_peaks
from tqdm import tqdm
import time


def main():
    file_path = "data\Edited full blank subtracted data set.csv"  # Update this path to your local CSV file
    z_range = range(1, 5)  # This will check for z = 1 to 5
    mass_error_ppm = 10  # Define the mass error in ppm

    # Start the progress bar
    with tqdm(total=100, desc="Processing peaks") as pbar:
        start_time = time.time()

        groups, unrelated_features, total_calculations = analyze_peaks(
            file_path, z_range, mass_error_ppm
        )

        # Simulate progress update
        pbar.update(100)

        end_time = time.time()
        elapsed_time = end_time - start_time

    # Print the number of groups identified
    print(f"Number of groups identified: {len(groups)}")

    # Print the groups of related peaks
    print("Groups of related peaks:")
    for group in groups:
        if len(group) > 2:
            print(f"Group: {sorted(group)}")

    # Print the number of unrelated features
    print(f"Number of unrelated features: {unrelated_features}")

    # Print the number of calculations performed
    print(f"Number of calculations performed: {total_calculations}")

    print(f"Script completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()
