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
    return array[j_start:j_end]


def group_by_mz_ppm(adjusted_df, mass_error_ppm):
    """Identify m/z groups within ±ppm and return a list of DataFrames per group."""
    mz_array = sorted(adjusted_df["m/z"].dropna())
    used = set()
    group_dfs = []

    for mz in mz_array:
        if mz in used:
            continue
        group_mz = find_similar_peaks(mz_array, mz, mass_error_ppm)
        group_mz = [val for val in group_mz if val not in used]

        if group_mz:
            group_df = adjusted_df[adjusted_df["m/z"].isin(group_mz)].copy()
            group_dfs.append(group_df)
            used.update(group_mz)
    return group_dfs


def optimal_ccs_grouping(group_dfs, ccs_tolerance=2.0):
    """
    Further split each m/z group (DataFrame) by CCS spread so that each subgroup has
    max CCS spread ≤ `ccs_tolerance` percent of the min CCS in the group.
    """
    final_groups = []

    for group_idx, group_df in enumerate(group_dfs, 1):
        group_df = group_df.sort_values(by="CCS").reset_index(drop=True)
        ccs_list = group_df["CCS"].tolist()

        i = 0
        n = len(ccs_list)

        while i < n:
            sub_indices = [i]
            sub_min_ccs = ccs_list[i]
            j = i + 1

            while j < n:
                max_ccs = max(ccs_list[i : j + 1])
                percent_diff = (max_ccs - sub_min_ccs) / sub_min_ccs * 100

                if percent_diff <= ccs_tolerance:
                    sub_indices.append(j)
                    j += 1
                else:
                    break

            sub_df = group_df.loc[sub_indices].copy()
            final_groups.append(sub_df)

            i += len(sub_indices)

    return final_groups


def optimal_rt_grouping(group_dfs, rt_tolerance=0.5):
    """
    Further split each group (DataFrame) by RT spread so that each subgroup has
    RT range ≤ `rt_tolerance` (in minutes).
    """
    final_groups = []

    for group_idx, group_df in enumerate(group_dfs, 1):
        group_df = group_df.sort_values(by="RT").reset_index(drop=True)
        rt_list = group_df["RT"].tolist()

        i = 0
        n = len(rt_list)

        while i < n:
            sub_indices = [i]
            rt_min = rt_list[i]
            j = i + 1

            while j < n:
                rt_max = max(rt_list[i : j + 1])
                rt_diff = rt_max - rt_min

                if rt_diff <= rt_tolerance:
                    sub_indices.append(j)
                    j += 1
                else:
                    break

            sub_df = group_df.loc[sub_indices].copy()
            final_groups.append(sub_df)

            print(f"\n[RT Subgroup] {len(sub_df)} peaks (Group {group_idx})")
            print(sub_df[["m/z", "RT"]].to_string(index=False))

            i += len(sub_indices)
    print(final_groups)
    return final_groups


def main():
    adjusted_df = pd.read_csv("PIMMS v1.2/Data_output/post_smearing_filter.csv")

    mass_error_ppm = 10
    ccs_tolerance = 2.0
    rt_tolerance = 0.5  # Set here and passed to RT filter

    mz_groups = group_by_mz_ppm(adjusted_df, mass_error_ppm)

    CCS_groups = optimal_ccs_grouping(mz_groups, ccs_tolerance)

    RT_groups = optimal_rt_grouping(CCS_groups, rt_tolerance)


if __name__ == "__main__":
    main()
