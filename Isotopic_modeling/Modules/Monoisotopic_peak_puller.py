import pandas as pd
from tqdm import tqdm


def calculate_mass_error(mass, mass_error_ppm, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    lower_bound = mass_error / z
    upper_bound = mass_error / z
    return lower_bound, upper_bound


def parse_and_sort_csv(file_path, mass_error_ppm):
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


def are_peaks_related(mass1, mass2, mass_error_ppm1, mass_error_ppm2, z, M):
    lower_bound1, upper_bound1 = calculate_mass_error(mass1, mass_error_ppm1, z)
    lower_bound2, upper_bound2 = calculate_mass_error(mass2, mass_error_ppm2, z)
    separation = abs(mass1 - mass2)
    maximum_separation = upper_bound2 + lower_bound1 + M / z
    minimum_separation = -lower_bound2 - upper_bound1 + M / z
    return separation <= maximum_separation and separation >= minimum_separation


def find_related_peaks_in_csv(file_path, z_range, M_range, mass_error_ppm):
    sorted_df = parse_and_sort_csv(file_path, mass_error_ppm)
    masses = sorted_df["m/z"].values
    iteration_count = 0
    related_peaks = []
    identified_features = set()
    child_peaks = set()
    parent_child_charge_states = {}

    for i in tqdm(range(len(masses)), desc="Processing peaks"):
        if masses[i] in child_peaks:
            continue
        for j in range(i + 1, len(masses)):
            mass1 = masses[i]
            mass2 = masses[j]
            iteration_count += 1
            match_found = False
            for z in z_range:
                for M in M_range:
                    if (mass1, mass2) in identified_features or (
                        mass2,
                        mass1,
                    ) in identified_features:
                        continue
                    if (
                        mass2 in parent_child_charge_states
                        and parent_child_charge_states[mass2] != z
                    ):
                        continue
                    if are_peaks_related(
                        mass1, mass2, mass_error_ppm, mass_error_ppm, z, M
                    ):
                        related_peaks.append((mass1, mass2, z, M, "collapsed feature"))
                        identified_features.add((mass1, mass2))
                        child_peaks.add(mass2)
                        parent_child_charge_states[mass2] = z
                        match_found = True
                        break  # Break the loop once a related peak is found
                if match_found:
                    break

    return related_peaks
