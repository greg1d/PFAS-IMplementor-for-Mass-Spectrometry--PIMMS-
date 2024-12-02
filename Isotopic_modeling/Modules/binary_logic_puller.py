# FILE: peak_analysis.py
import bisect
import pandas as pd


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


def expand_group(
    array,
    rt_array,
    ccs_array,
    initial_peak,
    initial_rt,
    initial_ccs,
    z_range,
    mass_error_ppm=10,
):
    group = [initial_peak]
    identified_features = set(group)
    i = array.index(initial_peak)
    peak_count = {i: 0}
    peak_charges = {i: []}
    calculations = 0

    # First iteration: work through all charges to identify all candidate peaks
    candidate_peaks = set()
    selected_z = None
    for z in z_range:
        peaks, calc = find_peaks_within_bounds(array, z, 1, i, mass_error_ppm)
        calculations += calc
        for peak in peaks:
            if (
                peak not in identified_features
                and abs(rt_array[array.index(peak)] - initial_rt) <= 0.2
                and abs(ccs_array[array.index(peak)] - initial_ccs) / initial_ccs
                <= 0.02
            ):
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
    if selected_z is not None and candidate_peaks:
        # Find the peak with the highest charge
        highest_charge_peak = max(candidate_peaks, key=lambda x: x[1])
        selected_z = highest_charge_peak[1]
        new_i = array.index(highest_charge_peak[0])
        print("new I", array[new_i], "RT:", rt_array[new_i], "CCS:", ccs_array[new_i])
        group.append(array[new_i])
        while True:
            new_peaks, calc = find_peaks_within_bounds(
                array, selected_z, 1, new_i, mass_error_ppm
            )
            calculations += calc
            if not new_peaks:
                break
            for new_peak in new_peaks:
                if (
                    new_peak not in identified_features
                    and abs(rt_array[array.index(new_peak)] - initial_rt) <= 0.2
                    and abs(ccs_array[array.index(new_peak)] - initial_ccs)
                    / initial_ccs
                    <= 0.02
                ):
                    identified_features.add(new_peak)
                    group.append(new_peak)
                    print(f"Peak: {new_peak}, Charge: {selected_z}, M: 1")
            new_i = array.index(
                new_peaks[-1]
            )  # Update new_i to the last identified peak

    return group, calculations


def analyze_peaks(file_path, z_range, mass_error_ppm=10):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Sort the DataFrame by the "m/z" column
    df = df.sort_values(by="m/z")

    # Extract the "m/z", "RT", and "CCS" columns as lists
    array = df["m/z"].tolist()
    rt_array = df["RT"].tolist()
    ccs_array = df["CCS"].tolist()

    identified_features = set()
    groups = []
    total_calculations = 0

    for i in range(len(array)):
        if array[i] not in identified_features:
            group, calculations = expand_group(
                array,
                rt_array,
                ccs_array,
                array[i],
                rt_array[i],
                ccs_array[i],
                z_range,
                mass_error_ppm,
            )
            total_calculations += calculations
            if len(group) >= 2:  # Only add groups with more than 2 features
                groups.append(group)
                identified_features.update(group)

    total_features = len(array)
    grouped_features = sum(len(group) for group in groups if len(group) >= 2)
    unrelated_features = total_features - grouped_features

    return groups, unrelated_features, total_calculations
