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


# Example usage
array = [102, 103, 104, 105, 106, 107]
z_range = range(1, 11)  # User-defined range for z from 1 to 10
M_range = range(1, 11)  # User-defined range for M from 1 to 10

total_calculations = 0
identified_features = set()
groups = []

print("Groups of related peaks:")
for group in groups:
    print(f"Group: {sorted(group)}")
