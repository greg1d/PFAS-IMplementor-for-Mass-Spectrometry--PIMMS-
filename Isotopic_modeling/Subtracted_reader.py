from Modules.Monoisotopic_peak_puller import find_related_peaks_in_csv


def main():
    file_path = "data/Dummy test blank subtracted data.csv"  # Update this path to your local CSV file
    z_range = range(1, 100)  # This will check for z = 1 to 99
    M_range = range(1, 11)  # This will check for M = 1 to 10
    mass_error_ppm = 10  # Define the mass error in ppm

    related_peaks, iteration_count, comparisons, parent_child_baby_relationships = (
        find_related_peaks_in_csv(file_path, z_range, M_range, mass_error_ppm)
    )

    # Print the related peaks
    for peak in related_peaks:
        print(f"Related peak: {peak}")

    # Print the number of calculations
    print(f"Number of calculations: {iteration_count}")

    # Print the summary of each comparison
    print("Summary of comparisons:")
    for comparison in comparisons:
        print(comparison)

    # Print the parent, child, and baby peaks
    print("Parent, Child, and Baby peaks:")
    for relationship in parent_child_baby_relationships:
        if relationship[2] == "parent-child":
            print(f"Parent peak: {relationship[0]}, Child peak: {relationship[1]}")
        elif relationship[2] == "baby":
            print(
                f"Baby peak: {relationship[1]} (related to Parent peak: {relationship[0]})"
            )


if __name__ == "__main__":
    main()
