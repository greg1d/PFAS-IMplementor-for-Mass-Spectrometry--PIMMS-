import bisect


def calculate_mass_error(mass, mass_error_ppm=10, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    mass_bound = mass_error / z
    return mass_bound


def find_peaks_within_bounds(array, z, M, i, mass_error_ppm=10):
    mass_bound = calculate_mass_error(array[i], mass_error_ppm, z)
    lower_bound = array[i] + (M / z) - mass_bound
    upper_bound = array[i] + (M / z) + mass_bound
    # Find the bounds using binary search
    j_start = bisect.bisect_left(array, lower_bound, i + 1)
    j_end = bisect.bisect_right(array, upper_bound, i + 1)

    # Collect all peaks within the bounds
    peaks_within_bounds = []
    for j in range(j_start, j_end):
        peaks_within_bounds.append(array[j])

    return peaks_within_bounds, j_end - j_start


def expand_group(array, initial_peak, z_range, M_range, mass_error_ppm=10):
    group = [initial_peak]
    identified_features = set(group)
    i = array.index(initial_peak)

    for z in z_range:
        for M in M_range:
            peaks, _ = find_peaks_within_bounds(array, z, M, i, mass_error_ppm)
            for peak in peaks:
                if peak not in identified_features:
                    identified_features.add(peak)
                    group.append(peak)
                    # Continue expanding the group with the new peak
                    for new_z in z_range:
                        for new_M in M_range:
                            new_peaks, _ = find_peaks_within_bounds(
                                array, new_z, new_M, array.index(peak), mass_error_ppm
                            )
                            for new_peak in new_peaks:
                                if new_peak not in identified_features:
                                    identified_features.add(new_peak)
                                    group.append(new_peak)

    return group


# Example usage
array = [102, 103, 104, 105, 106, 107]
z_range = range(1, 11)  # User-defined range for z from 1 to 10
M_range = range(1, 11)  # User-defined range for M from 1 to 10

total_calculations = 0
identified_features = set()
groups = []

for i in range(len(array)):
    if array[i] not in identified_features:
        group = expand_group(array, array[i], z_range, M_range)
        groups.append(group)
        identified_features.update(group)

print("Groups of related peaks:")
for group in groups:
    print(f"Group: {sorted(group)}")
