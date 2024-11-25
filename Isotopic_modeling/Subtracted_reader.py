from Modules.Monoisotopic_peak_puller import (
    parse_and_sort_csv,
    find_related_peaks_in_csv,
)

# User-defined variables
z_range = range(1, 2)  # This will check for z = 1 to 99
MASS_ERROR_PPM = 10  # Define the mass error in ppm


# User-defined variables
file_path = "data/Dummy test blank subtracted data.csv"  # Update this path to your local CSV file
z_range = range(1, 3)  # This will check for z = 1 to 99
mass_error_ppm = 10  # Define the mass error in ppm


def main():
    # Parse and sort the CSV file
    sorted_df = parse_and_sort_csv(file_path, mass_error_ppm)
    print(sorted_df)

    # Find related peaks in the CSV file
    related_peaks = find_related_peaks_in_csv(file_path, z_range, mass_error_ppm)
    print(f"Related peaks: {related_peaks}")


if __name__ == "__main__":
    main()
