from Modules.Monoisotopic_peak_puller import (
    find_related_peaks_in_csv,
)


def main():
    file_path = "data/Dummy test blank subtracted data.csv"  # Update this path to your local CSV file
    z_range = range(1, 100)  # This will check for z = 1 to 99
    M_range = range(1, 11)  # This will check for M = 1 to 10
    mass_error_ppm = 10  # Define the mass error in ppm

    related_peaks = find_related_peaks_in_csv(
        file_path, z_range, M_range, mass_error_ppm
    )
    print(f"Related peaks: {related_peaks}")


if __name__ == "__main__":
    main()
