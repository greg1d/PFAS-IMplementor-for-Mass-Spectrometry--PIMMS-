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


def expand_group(array, initial_peak, z_range, mass_error_ppm=10):
    group = [initial_peak]
    identified_features = set(group)
    i = array.index(initial_peak)
    peak_count = {i: 0}
    peak_charges = {i: []}

    # First iteration: work through all charges to identify all candidate peaks
    candidate_peaks = set()
    selected_z = None
    for z in z_range:
        peaks, _ = find_peaks_within_bounds(array, z, 1, i, mass_error_ppm)
        for peak in peaks:
            if peak not in identified_features:
                candidate_peaks.add((peak, z))
                peak_count[i] += 1
                peak_charges[i].append(z)
        if peaks and selected_z is None:
            selected_z = z

    # Report the i array point if exactly 2 peaks are identified
    if peak_count[i] >= 2:
        print(f"More than 2 peaks identified from array point {array[i]}")
        print(f"Charges of identified peaks: {peak_charges[i]}")

    # Second iteration: expand the group with the same charge `selected_z` and incrementing M
    if selected_z is not None:
        # Find the peak with the highest charge
        highest_charge_peak = max(candidate_peaks, key=lambda x: x[1])
        selected_z = highest_charge_peak[1]
        new_i = array.index(highest_charge_peak[0])
        print("new I", array[new_i])
        group.append(array[new_i])
        while True:
            new_peaks, _ = find_peaks_within_bounds(
                array, selected_z, 1, new_i, mass_error_ppm
            )
            if not new_peaks:
                break
            for new_peak in new_peaks:
                if new_peak not in identified_features:
                    identified_features.add(new_peak)
                    group.append(new_peak)
                    print(f"Peak: {new_peak}, Charge: {selected_z}, M: 1")

            new_i = array.index(
                new_peaks[-1]
            )  # Update new_i to the last identified peak
    return group


# Example usage
array = [102, 103, 104, 110, 111, 100000]
z_range = range(1, 4)  # User-defined range for z from 1 to 3

total_calculations = 0
identified_features = set()
groups = []

for i in range(len(array)):
    if array[i] not in identified_features:
        group = expand_group(array, array[i], z_range)
        groups.append(group)
        identified_features.update(group)

print("Groups of related peaks:")
for group in groups:
    print(f"Group: {sorted(group)}")
