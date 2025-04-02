import bisect
import pandas as pd


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, mass, mass_error_ppm=10):
    """Finds peaks within the mass error bounds using binary search."""
    mass_bound = calculate_mass_error_no_charge(mass, mass_error_ppm)
    lower_bound = mass - mass_bound
    upper_bound = mass + mass_bound

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    print(array[j_start:j_end])
    return array[j_start:j_end]


def group_by_mz_ppm(adjusted_df, mass_error_ppm):
    """Identify groups of m/z values within ±ppm."""
    mz_array = sorted(adjusted_df["m/z"].dropna())
    used = set()
    groups = []

    for mz in mz_array:
        if mz in used:
            continue
        group = find_similar_peaks(mz_array, mz, mass_error_ppm)
        group = [val for val in group if val not in used]
        if group:
            groups.append(group)
            used.update(group)

    # Debug print
    for i, group in enumerate(groups, 1):
        print(f"\n[Group {i}] ({len(group)} peaks)")
        for mz in group:
            print(f"  m/z = {mz:.6f}")

    return groups


def main():
    # Example adjusted_df with rows to process
    adjusted_df = pd.read_csv("PIMMS v1.2/Data_output/post_smearing_filter.csv")

    mass_error_ppm = 10
    rt_tolerance = 0.5
    ccs_tolerance = 2.0

    # Identify groups
    groups = group_by_mz_ppm(adjusted_df, mass_error_ppm)
    # Merge groups into a single feature
    print(f"\n[INFO] Total groups identified: {len(groups)}")


if __name__ == "__main__":
    main()
