import pandas as pd


def calculate_mass_error(mass, mass_error_ppm):
    """
    Calculate the mass error and the corresponding mass range.

    Parameters:
    mass (float): The actual mass.
    mass_error_ppm (float): The mass error in parts per million (ppm).

    Returns:
    tuple: A tuple containing the lower and upper bounds of the mass range.
    """
    mass_error = mass * mass_error_ppm * 1e-6
    lower_bound = mass - mass_error
    upper_bound = mass + mass_error
    return lower_bound, upper_bound


def parse_and_sort_csv(file_path, mass_error_ppm):
    print(file_path)
    df = pd.read_csv(file_path)
    # Check if 'm/z' column exists
    if "m/z" not in df.columns:
        raise ValueError("The CSV file does not contain an 'm/z' column.")

    # Sort the DataFrame by the 'm/z' column
    sorted_df = df.sort_values(by="m/z")

    # Calculate the mass error in absolute terms
    sorted_df["mass_error"] = sorted_df["m/z"] * mass_error_ppm * 1e-6

    return sorted_df


# User-defined variable for mass error in ppm
mass_error_ppm = 10

# Example usage of the calculate_mass_error function
actual_mass = 200
lower_bound, upper_bound = calculate_mass_error(actual_mass, mass_error_ppm)
print(
    f"Mass range for {actual_mass} with {mass_error_ppm} ppm error: {lower_bound} to {upper_bound}"
)

# Use the function with the specified CSV file and mass error
sorted_df = parse_and_sort_csv(
    "Isotopic_modeling/data/dummy blank subtracted file.csv", mass_error_ppm
)
