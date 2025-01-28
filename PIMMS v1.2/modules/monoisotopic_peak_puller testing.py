import pandas as pd
import bisect


def calculate_mass_error(mass, mass_error_ppm=10, z=1):
    mass_error = mass * mass_error_ppm * 1e-6
    return mass_error / z


def find_peaks_within_bounds(array, z, M, i, mass_error_ppm=10):
    mass_bound = calculate_mass_error(array[i], mass_error_ppm, z)
    lower_bound = array[i] + (M / z) - mass_bound
    upper_bound = array[i] + (M / z) + mass_bound
    j_start = bisect.bisect_left(array, lower_bound, i + 1)
    j_end = bisect.bisect_right(array, upper_bound, i + 1)
    return array[j_start:j_end], j_end - j_start


def expand_group(
    adjusted_df,
    initial_peak,
    initial_rt,
    initial_ccs,
    z_range,
    mass_error_ppm=10,
    rt_tolerance=0.5,
    ccs_tolerance=2.0,
):
    array = adjusted_df["m/z"].tolist()
    rt_array = adjusted_df["RT"].tolist()
    ccs_array = adjusted_df["CCS"].tolist()

    group = [initial_peak]
    identified_features = set(group)
    to_process = [initial_peak]

    while to_process:
        current_peak = to_process.pop(0)
        current_idx = array.index(current_peak)
        current_rt = rt_array[current_idx]
        current_ccs = ccs_array[current_idx]

        for z in z_range:
            peaks, _ = find_peaks_within_bounds(
                array, z, 1, current_idx, mass_error_ppm
            )
            for peak in peaks:
                idx = array.index(peak)
                if (
                    peak not in identified_features
                    and abs(rt_array[idx] - current_rt) <= rt_tolerance
                    and abs(ccs_array[idx] - current_ccs) / current_ccs * 100
                    <= ccs_tolerance
                ):
                    identified_features.add(peak)
                    group.append(peak)
                    to_process.append(peak)

    return group


def analyze_adjusted_df(
    adjusted_df,
    z_range=range(1, 4),
    mass_error_ppm=10,
    rt_tolerance=0.5,
    ccs_tolerance=2.0,
):
    adjusted_df = adjusted_df.sort_values(by="m/z")
    array = adjusted_df["m/z"].tolist()

    identified_features = set()
    groups = []

    for i in range(len(array)):
        if array[i] not in identified_features:
            group = expand_group(
                adjusted_df,
                array[i],
                adjusted_df["RT"].iloc[i],
                adjusted_df["CCS"].iloc[i],
                z_range,
                mass_error_ppm,
                rt_tolerance,
                ccs_tolerance,
            )
            if len(group) > 1:
                groups.append(group)
                identified_features.update(group)

    return groups


def main():
    # Example usage with adjusted_df
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3.666, 5, 3.666, 3.666, 3.666],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 175.79, 175.79, 175.79, 175.79],
            "m/z": [277.2320, 278.2320, 279.2320, 280.2320, 281.2320],
            "148 B2 16632.d.DeMP": [361274.0, 327743.0, 423382.0, 155202.0, 416438.0],
            "149 B2 16631.d.DeMP": [361731.0, 324716.0, 422827.0, 154871.0, 416854.0],
        }
    )

    z_range = range(1, 4)
    mass_error_ppm = 10
    rt_tolerance = 0.5
    ccs_tolerance = 2.0

    groups = analyze_adjusted_df(
        adjusted_df, z_range, mass_error_ppm, rt_tolerance, ccs_tolerance
    )

    print(f"Number of groups identified: {len(groups)}")
    for group in groups:
        print(f"Group: {group}")


if __name__ == "__main__":
    main()
