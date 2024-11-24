import pandas as pd

# Define the mass error in ppm as a constant
MASS_ERROR_PPM = 10


def calculate_mass_error(mass, mass_error_ppm=MASS_ERROR_PPM):
    mass_error = mass * mass_error_ppm * 1e-6
    lower_bound = mass - mass_error
    upper_bound = mass + mass_error
    return lower_bound, upper_bound


def parse_and_sort_csv(file_path, mass_error_ppm=MASS_ERROR_PPM):
    print(file_path)
    df = pd.read_csv(file_path)
    # Check if 'm/z' column exists
    if "m/z" not in df.columns:
        raise ValueError("The CSV file does not contain an 'm/z' column.")

    # Sort the DataFrame by the 'm/z' column
    sorted_df = df.sort_values(by="m/z")

    # Calculate the mass error in absolute terms using the calculate_mass_error function
    sorted_df["mass_error"] = sorted_df["m/z"].apply(
        lambda x: calculate_mass_error(x, mass_error_ppm)[1] - x
    )

    return sorted_df


def are_peaks_related(
    mass1, mass2, mass_error_ppm1=MASS_ERROR_PPM, mass_error_ppm2=MASS_ERROR_PPM, z=1
):
    _, upper_bound1 = calculate_mass_error(mass1, mass_error_ppm1)
    _, upper_bound2 = calculate_mass_error(mass2, mass_error_ppm2)
    separation = abs(mass1 - mass2)
    acceptable_error1 = upper_bound1 - mass1
    acceptable_error2 = upper_bound2 - mass2
    print(separation)
    print(acceptable_error1)
    print(acceptable_error2)
    lower_bound = (separation - (acceptable_error1 + acceptable_error2)) / z
    upper_bound = (separation + (acceptable_error1 + acceptable_error2)) / z
    return lower_bound < separation < upper_bound


def find_related_peaks(mass1, mass2, z_range, mass_error_ppm=MASS_ERROR_PPM):
    related_z = []
    for z in z_range:
        if are_peaks_related(mass1, mass2, mass_error_ppm, mass_error_ppm, z):
            related_z.append(z)
    return related_z


# Example usage
mass1 = 100
mass2 = 101
z_range = range(1, 5)  # This will check for z = 1, 2, 3, 4

related_z = find_related_peaks(mass1, mass2, z_range)
print(f"Charge states where the peaks are related: {related_z}")
