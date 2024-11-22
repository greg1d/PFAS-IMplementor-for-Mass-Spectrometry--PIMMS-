import pandas as pd


def parse_and_sort_csv(file_path, mass_error_ppm):
    # Read the CSV file into a DataFrame
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

# Use the function with the specified CSV file and mass error
sorted_df = parse_and_sort_csv("dummy blank subtracted file.csv", mass_error_ppm)
print(sorted_df[["m/z", "mass_error"]])
