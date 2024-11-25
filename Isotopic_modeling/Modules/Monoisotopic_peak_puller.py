import pandas as pd
import numpy as np

# Define the mass error in ppm as a constant
MASS_ERROR_PPM = 10
mass1 = 100
mass2 = 100.5
z_range = range(1, 100)  # This will check for z = 1, 2


def calculate_mass_error(mass, mass_error_ppm=MASS_ERROR_PPM, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    lower_bound = mass_error / z
    upper_bound = mass_error / z
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

def are_peaks_related(mass1, mass2, mass_error_ppm1=MASS_ERROR_PPM, mass_error_ppm2=MASS_ERROR_PPM, z=z_range):
    lower_bound1, upper_bound1 = calculate_mass_error(mass1, mass_error_ppm1, z)
    lower_bound2, upper_bound2 = calculate_mass_error(mass2, mass_error_ppm2, z)
    separation = abs(mass1 - mass2)
    maximum_separation = upper_bound2 + lower_bound1 + 1/z
    minimum_separation = -lower_bound2 - upper_bound1 + 1/z

    # Print bounds to 5 decimal places
    print(f"Upper Bound 1: {upper_bound1:.5f}, Lower Bound 1: {lower_bound1:.5f}")
    print(f"Upper Bound 2: {upper_bound2:.5f}, Lower Bound 2: {lower_bound2:.5f}")
    print(f"Maximum Separation: {maximum_separation:.5f}")
    print(f"Minimum Separation: {minimum_separation:.5f}")
    print(separation)
    return separation <= maximum_separation and separation >= minimum_separation


def find_related_peaks(mass1, mass2, z_range, mass_error_ppm=MASS_ERROR_PPM):
    iteration_count = 0
    for z in z_range:
        iteration_count += 1
        if are_peaks_related(mass1, mass2, mass_error_ppm, mass_error_ppm, z):
            print(f"Number of iterations: {iteration_count}")
            return z  # Return the charge state that satisfies the condition
    print(f"Number of iterations: {iteration_count}")
    return None  # Return None if no related peaks are found

# Example usage

related_z = find_related_peaks(mass1, mass2, z_range)
print(f"Charge state where the peaks are related: {related_z}")