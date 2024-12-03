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
    id_array,
    initial_peak,
    initial_rt,
    initial_ccs,
    initial_id,
    z_range,
    mass_error_ppm=10,
):
    group = [(initial_peak, initial_id)]
    identified_features = set([initial_id])
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
            peak_id = id_array[array.index(peak)]
            if (
                peak_id not in identified_features
                and abs(rt_array[array.index(peak)] - initial_rt) <= 0.2
                and abs(ccs_array[array.index(peak)] - initial_ccs) / initial_ccs
                <= 0.02
            ):
                candidate_peaks.add((peak, peak_id, z))
                peak_count[i] += 1
                peak_charges[i].append(z)
                # Debugging statement to print RT values of the rows being compared
                print(
                    f"Comparing RT values: Initial RT = {initial_rt}, Peak RT = {rt_array[array.index(peak)]}"
                )
        if peaks and selected_z is None:
            selected_z = z

    # Report the i array point if exactly 2 peaks are identified
    if peak_count[i] >= 2:
        print(f"More than 2 peaks identified from array point {array[i]}")
        print(f"Charges of identified peaks: {peak_charges[i]}")

    # Second iteration: expand the group with the same charge `selected_z` and incrementing M
    if selected_z is not None and candidate_peaks:
        # Find the peak with the highest charge
        highest_charge_peak = max(candidate_peaks, key=lambda x: x[2])
        selected_z = highest_charge_peak[2]
        new_i = array.index(highest_charge_peak[0])
        print("new I", array[new_i], "RT:", rt_array[new_i], "CCS:", ccs_array[new_i])
        group.append((array[new_i], id_array[new_i]))
        while True:
            new_peaks, calc = find_peaks_within_bounds(
                array, selected_z, 1, new_i, mass_error_ppm
            )
            calculations += calc
            if not new_peaks:
                break
            for new_peak in new_peaks:
                new_peak_id = id_array[array.index(new_peak)]
                if (
                    new_peak_id not in identified_features
                    and abs(rt_array[array.index(new_peak)] - initial_rt) <= 0.2
                    and abs(ccs_array[array.index(new_peak)] - initial_ccs)
                    / initial_ccs
                    <= 0.02
                ):
                    identified_features.add(new_peak_id)
                    group.append((new_peak, new_peak_id))
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

    # Extract the "m/z", "RT", "CCS", and "ID" columns as lists
    array = df["m/z"].tolist()
    rt_array = df["RT"].tolist()
    ccs_array = df["CCS"].tolist()
    id_array = df["ID"].tolist()

    identified_features = set()
    groups = []
    total_calculations = 0

    for i in range(len(array)):
        if id_array[i] not in identified_features:
            group, calculations = expand_group(
                array,
                rt_array,
                ccs_array,
                id_array,
                array[i],
                rt_array[i],
                ccs_array[i],
                id_array[i],
                z_range,
                mass_error_ppm,
            )
            total_calculations += calculations
            if len(group) >= 2:  # Only add groups with more than 2 features
                groups.append(group)
                identified_features.update([id for _, id in group])

    total_features = len(array)
    grouped_features = sum(len(group) for group in groups if len(group) >= 2)
    unrelated_features = total_features - grouped_features

    return groups, unrelated_features, total_calculations


def main():
    file_path = "data/Edited full blank subtracted data set.csv"  # Update this path to your local CSV file
    z_range = range(1, 5)  # This will check for z = 1 to 5
    mass_error_ppm = 10  # Define the mass error in ppm

    # Load the data to get RT, CCS, and ID values
    data_df = pd.read_csv(file_path)
    rt_ccs_mapping = data_df.set_index("ID").to_dict("index")

    # Run the operation
    groups, unrelated_features, total_calculations = analyze_peaks(
        file_path, z_range, mass_error_ppm
    )

    # Print the number of groups identified
    print(f"Number of groups identified: {len(groups)}")

    # Print the groups of related peaks
    print("Groups of related peaks:")
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}: {sorted(group)}")

    # Print the number of unrelated features
    print(f"Number of unrelated features: {unrelated_features}")

    # Print the number of calculations performed
    print(f"Number of calculations performed: {total_calculations}")

    print("Script completed")

    # Export the results to a CSV file
    results = []
    for idx, group in enumerate(groups):
        for peak, peak_id in group:
            # Extract RT, CCS, and ID values from the mapping using the ID
            rt_value = rt_ccs_mapping.get(peak_id, {}).get("RT", "N/A")
            ccs_value = rt_ccs_mapping.get(peak_id, {}).get("CCS", "N/A")
            id_value = rt_ccs_mapping.get(peak_id, {}).get("ID", "N/A")
            results.append(
                {
                    "Group": idx + 1,
                    "Peak": peak,
                    "ID": peak_id,
                    "RT": rt_value,
                    "CCS": ccs_value,
                }
            )

    results_df = pd.DataFrame(results)
    results_df.to_csv("analyzed_peaks_results.csv", index=False)
    print("Results saved to analyzed_peaks_results.csv")


if __name__ == "__main__":
    main()
