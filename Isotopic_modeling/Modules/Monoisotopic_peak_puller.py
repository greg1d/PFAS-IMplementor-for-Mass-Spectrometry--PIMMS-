import pandas as pd


def parse_and_sort_csv(file_path, mass_error_ppm):
    # Placeholder for the actual implementation of parsing and sorting the CSV file
    df = pd.read_csv(file_path)
    df = df.sort_values(by=["m/z"])
    return df


def calculate_mass_error(mass, mass_error_ppm, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    lower_bound = mass_error / z
    upper_bound = mass_error / z
    return lower_bound, upper_bound


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
    parent_peaks = set()
    parent_child_charge_states = {}
    comparisons = []
    completed_features = set()
    parent_child_baby_relationships = []
    collapsed_features = {}

    for i in range(len(masses)):
        if masses[i] in completed_features:
            continue
        current_group = [masses[i]]
        first_child_z = None
        max_mass_difference = None
        for j in range(i + 1, len(masses)):
            mass1 = masses[i]
            mass2 = masses[j]
            if (
                max_mass_difference is not None
                and (mass2 - mass1) > max_mass_difference
            ):
                break
            iteration_count += 1
            comparisons.append(f"Peak {mass1} compared with Peak {mass2}")
            match_found = False
            for z in z_range:
                if first_child_z is not None and z != first_child_z:
                    continue
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
                        parent_peaks.add(mass1)
                        parent_child_charge_states[mass2] = z
                        parent_child_baby_relationships.append(
                            (mass1, mass2, "parent-child")
                        )
                        current_group.append(mass2)
                        if first_child_z is None:
                            first_child_z = z
                            max_mass_difference = M_range[-1] / z
                        match_found = True
                        break  # Break the loop once a related peak is found
                if match_found:
                    break

        # Identify the "baby" peak as the highest mass peak in the current group
        if current_group:
            baby_peak = max(current_group)
            if len(current_group) == 1:
                parent_child_baby_relationships.append((masses[i], baby_peak, "loner"))
                collapsed_features[masses[i]] = current_group
            else:
                parent_child_baby_relationships.append((masses[i], baby_peak, "baby"))
                collapsed_features[masses[i]] = current_group
            completed_features.update(current_group)
            completed_features.add(masses[i])
            # Mark the entire group as completed
            for peak in current_group:
                completed_features.add(peak)

    return (
        related_peaks,
        iteration_count,
        comparisons,
        parent_child_baby_relationships,
        collapsed_features,
    )
