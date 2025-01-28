import pandas as pd

from blank_subtraction import find_peaks_within_bounds


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

    # First iteration: work through all charges to identify all candidate peaks
    candidate_peaks = set()
    selected_z = None
    for z in z_range:
        peaks, _ = find_peaks_within_bounds(array, z, 1, i, mass_error_ppm)
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

    # Second iteration: expand the group with the same charge `selected_z` and incrementing M
    if selected_z is not None and candidate_peaks:
        # Find the peak with the highest charge
        highest_charge_peak = max(candidate_peaks, key=lambda x: x[1])
        selected_z = highest_charge_peak[1]
        new_i = array.index(highest_charge_peak[0])
        group.append(array[new_i])
        while True:
            new_peaks, _ = find_peaks_within_bounds(
                array, selected_z, 1, new_i, mass_error_ppm
            )
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
            new_i = array.index(
                new_peaks[-1]
            )  # Update new_i to the last identified peak

    return group


# Example usage
def main():
    # Read the CSV file
    df = pd.read_csv("PIMMS v1.2/data/debugging_data_set.csv")

    # Sort the DataFrame by the "m/z" column
    df = df.sort_values(by="m/z")

    # Extract the "m/z", "RT", and "CCS" columns as lists
    array = df["m/z"].tolist()
    rt_array = df["RT"].tolist()
    ccs_array = df["CCS"].tolist()

    z_range = range(1, 4)  # User-defined range for z from 1 to 3

    identified_features = set()
    groups = []

    for i in range(len(array)):
        if array[i] not in identified_features:
            group = expand_group(
                array, rt_array, ccs_array, array[i], rt_array[i], ccs_array[i], z_range
            )
            if len(group) >= 2:  # Only add groups with more than 2 features
                groups.append(group)
                identified_features.update(group)

    print(f"Number of groups identified: {len(groups)}")
    print("Groups identified:")

    # Print each group with its details
    for idx, group in enumerate(groups, start=1):
        print(f"Group {idx}: {group}")

    total_features = len(array)
    grouped_features = sum(len(group) for group in groups if len(group) >= 2)
    unrelated_features = total_features - grouped_features

    print(f"Number of unrelated features: {unrelated_features}")


if __name__ == "__main__":
    main()
