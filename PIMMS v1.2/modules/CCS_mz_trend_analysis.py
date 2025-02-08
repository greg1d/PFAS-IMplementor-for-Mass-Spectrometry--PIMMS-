import time

import numpy as np
import pandas as pd
from scipy.stats import linregress

# Define repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "HF": 20.006228,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "CH2CHF": 46.021878,
    "CH2CH2CF2CF2": 128.024912,
    "CF2CFCl": 115.964062,
    "CH2CH2CF2CFCl": 143.995362,
    "OCF2CFCF3": 165.985333,
}


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=[]):
    """Identifies homologous series trends by sequentially checking different repeating units.
    Ensures unique groups based on ID values while allowing a single peak to appear in multiple homologous series.
    """

    import time

    start_time = time.perf_counter()
    iteration_count = 0  # Track loop iterations

    # Convert user-provided repeating units into masses
    selected_units = {
        unit: REPEATING_UNITS[unit]
        for unit in repeating_units
        if unit in REPEATING_UNITS
    }

    # **Sort data by m/z for efficient searching**
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)

    unique_group_ids = set()
    mass_groups = []

    print(f"[DEBUG] Total data points: {len(adjusted_df)}")

    for unit_name, M in selected_units.items():
        print(
            f"\n[INFO] Searching for homologous series with repeating unit: {unit_name} (M = {M:.6f})"
        )
        processed_indices = set()

        for i in range(len(adjusted_df)):
            iteration_count += 1
            if i in processed_indices:
                continue

            mz_value = adjusted_df.at[i, "m/z"]
            current_group = [
                {
                    "m/z": mz_value,
                    "ID": adjusted_df.at[i, "ID"],
                    "CCS": adjusted_df.at[i, "CCS"],
                    "Classification Type": adjusted_df.at[i, "Classification Type"],
                    "Match Source": adjusted_df.at[i, "Match Source"],
                    "Match": adjusted_df.at[i, "Match"],
                    "Repeating Unit": unit_name,
                }
            ]
            processed_indices.add(i)

            search_queue = [i]

            while search_queue:
                current_idx = search_queue.pop(0)
                current_mz = adjusted_df.at[current_idx, "m/z"]

                for j in range(current_idx + 1, len(adjusted_df)):
                    iteration_count += 1
                    if j in processed_indices:
                        continue

                    next_mz_value = adjusted_df.at[j, "m/z"]
                    mass_diff = abs(current_mz - next_mz_value)
                    ppm_tolerance = (mass_error_ppm / 1e6) * current_mz

                    if mass_diff <= ppm_tolerance or any(
                        abs(mass_diff - M * k) <= ppm_tolerance for k in range(1, 3)
                    ):
                        current_group.append(
                            {
                                "m/z": next_mz_value,
                                "ID": adjusted_df.at[j, "ID"],
                                "CCS": adjusted_df.at[j, "CCS"],
                                "Classification Type": adjusted_df.at[
                                    j, "Classification Type"
                                ],
                                "Match Source": adjusted_df.at[j, "Match Source"],
                                "Match": adjusted_df.at[j, "Match"],
                                "Repeating Unit": unit_name,
                            }
                        )
                        processed_indices.add(j)
                        search_queue.append(j)

            # **Ensure the group has at least 3 points before performing ppm separation**
            if len(current_group) < 3:
                print(
                    f"[WARNING] Group with {len(current_group)} points is too small. Skipping ppm separation."
                )
                print(pd.DataFrame(current_group).to_string(index=False))  # Debug print
                continue  # Skip storing this group

            # **Apply ppm separation only within detected groups**
            min_mz = min(entry["m/z"] for entry in current_group)
            max_mz = max(entry["m/z"] for entry in current_group)
            ppm_separation = (abs(max_mz - min_mz) / min_mz) * 1e6

            if ppm_separation < 10:
                print(
                    f"[WARNING] Group rejected due to insufficient ppm separation ({ppm_separation:.2f} ppm)."
                )
                print(pd.DataFrame(current_group).to_string(index=False))  # Debug print
                continue  # Skip storing this group

            # **Ensure the group is unique and store it**
            group_ids = frozenset(entry["ID"] for entry in current_group)
            if group_ids not in unique_group_ids:
                unique_group_ids.add(group_ids)
                group_df = pd.DataFrame(current_group)
                mass_groups.append(group_df)

                # **Debugging: Print Group Composition**
                print(
                    f"\n[DEBUG] Identified Group {len(mass_groups)} - Homologous Series (Repeating Unit: {unit_name}):"
                )
                print(
                    group_df.to_string(index=False)
                )  # Print clean table without row index
                print("-" * 80)  # Separator for readability

    total_time = time.perf_counter() - start_time
    print(
        f"\n[INFO] Mass repeating unit analysis completed in {total_time:.4f} seconds."
    )
    print(
        f"[METRIC] Total iterations: {iteration_count}, Processing speed: {iteration_count / total_time:.2f} iters/sec"
    )

    return mass_groups


def CCS_v_mz_analysis(mass_groups, significance_cutoff=0.05):
    """
    Performs correlation analysis to classify homologous series.
    Adds PSU metrics to assess computational efficiency.
    """

    print("\n[DEBUG] Starting CCS_v_mz_analysis function...")

    if mass_groups.empty:
        print("[ERROR] Received empty group list. Exiting function.")
        return [], [], [], []

    start_time = time.perf_counter()
    iteration_count = 0

    data_points = list(zip(mass_groups["m/z"], mass_groups["CCS"]))
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    if len(mz_values) < 3:
        print(
            "[WARNING] Not enough points to fit a regression model. Returning as mass_only_group."
        )
        return [], [], [], data_points

    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    if p_value <= significance_cutoff and slope > 0:
        print("[INFO] Initial group meets significance and is positively correlated.")
        return data_points, [], [], []

    remaining_points = data_points.copy()
    post_source_decay = []
    branched_isomer = []

    while len(remaining_points) > 2:
        iteration_count += 1
        mz_values = np.array([p[0] for p in remaining_points])
        ccs_values = np.array([p[1] for p in remaining_points])
        slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)

        if p_value <= significance_cutoff and slope > 0:
            print(
                f"[INFO] Significant positive correlation achieved with {len(remaining_points)} points."
            )
            return remaining_points, post_source_decay, branched_isomer, []

        residuals = [
            abs(ccs - (slope * mz + intercept)) for mz, ccs in remaining_points
        ]
        max_residual_idx = np.argmax(residuals)
        worst_point = remaining_points.pop(max_residual_idx)

        predicted_ccs = slope * worst_point[0] + intercept
        full_point_metadata = (
            mass_groups.loc[mass_groups["m/z"] == worst_point[0]].iloc[0].to_dict()
        )

        if worst_point[1] > predicted_ccs:
            full_point_metadata["Classification"] = "Post Source Decay"
            post_source_decay.append(full_point_metadata)
        else:
            full_point_metadata["Classification"] = "Branched Isomer"
            branched_isomer.append(full_point_metadata)

    total_time = time.perf_counter() - start_time
    print(
        f"\n[METRIC] Total iterations: {iteration_count}, Processing speed: {iteration_count / total_time:.2f} iters/sec"
    )

    return [], [], [], data_points


def main():
    """Run the analysis and interactive plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)
    repeating_units = ["CF2", "OCF2"]

    print(
        f"\n[INFO] Running mz_repeating_unit_analysis with repeating units: {repeating_units}"
    )
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    if not mass_groups:
        print("[WARNING] No homologous series found. Exiting...")
        return

    for idx, mass_group in enumerate(mass_groups):
        print(f"\n[DEBUG] Processing Mass Group {idx + 1}:")
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(mass_group)
        )


if __name__ == "__main__":
    main()
