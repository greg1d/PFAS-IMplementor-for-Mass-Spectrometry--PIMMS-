import numpy as np
import pandas as pd
from scipy.stats import linregress

# Define repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=[]):
    """Identifies homologous series trends by sequentially checking different repeating units.
    Ensures unique groups based on ID values while allowing a single peak to appear in multiple homologous series.
    """

    iteration_count = 0  # Track loop iterations
    group_counter = 0  # Track unique Group ID

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

    for unit_name, M in selected_units.items():
        processed_indices = set()

        for i in range(len(adjusted_df)):
            iteration_count += 1
            if i in processed_indices:
                continue

            mz_value = adjusted_df.at[i, "m/z"]
            group_counter += 1  # Assign new unique GroupID

            current_group = [
                {
                    "GroupID": group_counter,  # Assign Group ID
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

                    if any(
                        abs(mass_diff - M * k) <= ppm_tolerance for k in range(1, 3)
                    ):
                        current_group.append(
                            {
                                "GroupID": group_counter,  # Keep same Group ID
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

            # **Only process groups that have at least 3 points BEFORE expansion**
            if len(current_group) <= 3:
                continue  # Skip storing this group

            # **Ensure min-max m/z difference is at least 10**
            min_mz = min(entry["m/z"] for entry in current_group)
            max_mz = max(entry["m/z"] for entry in current_group)
            if max_mz - min_mz < 10:
                continue  # Skip storing this group

            # **Ensure the group is unique and store it**
            group_ids = frozenset(entry["ID"] for entry in current_group)
            if group_ids not in unique_group_ids:
                unique_group_ids.add(group_ids)
                group_df = pd.DataFrame(current_group)
                mass_groups.append(group_df)

                # **Debugging: Print Group Composition**

    # **Combine all groups into a single DataFrame**
    if mass_groups:
        mass_groups = pd.concat(mass_groups, ignore_index=True)
    else:
        mass_groups = pd.DataFrame(
            columns=[
                "GroupID",
                "m/z",
                "ID",
                "CCS",
                "Classification Type",
                "Match Source",
                "Match",
                "Repeating Unit",
            ]
        )

    return mass_groups


def CCS_v_mz_analysis(mass_groups, significance_cutoff=0.05):
    """
    Performs correlation analysis to classify homologous series.
    If a statistically significant trend is found, returns as an IM_group.
    If no trend is found, returns as a mass_only_group.
    Adds debugging statements to help understand the execution flow.
    """

    print("\n[DEBUG] Starting CCS_v_mz_analysis function...")

    if mass_groups.empty:
        print("[ERROR] Received empty group list. Exiting function.")
        return [], [], [], []

    iteration_count = 0

    # Extract m/z and CCS values
    data_points = list(zip(mass_groups["m/z"], mass_groups["CCS"]))
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    # If there are fewer than 3 points, return as mass_only_group
    if len(mz_values) < 3:
        print(
            "[WARNING] Not enough points to fit a regression model. Returning as mass_only_group."
        )
        return [], [], [], data_points  # Return in mass_only_group

    # Perform linear regression
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    print(
        f"[DEBUG] Initial regression results: slope={slope:.5f}, r_squared={r_squared:.5f}, p_value={p_value:.5f}"
    )

    # If the initial group meets significance and is positively correlated, return as IM_group
    if p_value <= significance_cutoff and slope > 0:
        print(
            "[INFO] Initial group meets significance and is positively correlated. Returning as IM_group."
        )
        return data_points, [], [], []  # Return in IM_group

    # Iteratively refine the dataset to check if any subset meets the significance criteria
    remaining_points = data_points.copy()
    post_source_decay = []
    branched_isomer = []

    while len(remaining_points) > 2:
        iteration_count += 1

        mz_values = np.array([p[0] for p in remaining_points])
        ccs_values = np.array([p[1] for p in remaining_points])
        slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)

        print(
            f"[DEBUG] Iteration {iteration_count}: slope={slope:.5f}, r_squared={r_squared:.5f}, p_value={p_value:.5f}"
        )

        if p_value <= significance_cutoff and slope > 0:
            print(
                f"[INFO] Significant positive correlation achieved with {len(remaining_points)} points. Returning as IM_group."
            )
            return remaining_points, post_source_decay, branched_isomer, []

        # Find and remove the worst outlier (highest residual)
        residuals = [
            abs(ccs - (slope * mz + intercept)) for mz, ccs in remaining_points
        ]
        max_residual_idx = np.argmax(residuals)
        worst_point = remaining_points.pop(max_residual_idx)

        predicted_ccs = slope * worst_point[0] + intercept
        full_point_metadata = (
            mass_groups.loc[mass_groups["m/z"] == worst_point[0]].iloc[0].to_dict()
        )

        # Classify the removed point
        if worst_point[1] > predicted_ccs:
            full_point_metadata["Classification"] = "Post Source Decay"
            post_source_decay.append(full_point_metadata)
        else:
            full_point_metadata["Classification"] = "Branched Isomer"
            branched_isomer.append(full_point_metadata)

        print(
            f"[DEBUG] Removed outlier with m/z={worst_point[0]:.5f}, classified as {full_point_metadata['Classification']}"
        )

    # If no significant trend was found, return as mass_only_group
    print(
        "[WARNING] No statistically significant trend found. Returning as mass_only_group."
    )
    return [], [], [], data_points


def main():
    """Run the full analysis pipeline: Identify homologous series, analyze trends, and classify groups."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)
    repeating_units = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]

    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups were identified.")
        return

    # Storage for classified groups
    IM_groups = []
    mass_only_groups = []

    # Treat each mass group independently
    for idx, (group_id, group_df) in enumerate(
        mass_groups.groupby("GroupID")
    ):  # Process each group separately
        print(f"\n[DEBUG] Analyzing Mass Group {idx + 1}:")

        # Print the received group before analysis
        print("\n[DEBUG] Received Mass Group for Analysis:")
        print(group_df.to_string(index=False))

        # Perform correlation analysis
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        if IM_group:  # If a statistically significant trend is found
            print(f"[INFO] Mass Group {idx + 1} classified as IM_group.")
            IM_groups.append(pd.DataFrame(IM_group, columns=["m/z", "CCS"]))
        else:  # If no significant trend is found, classify as mass_only_group
            print(
                f"[WARNING] Mass Group {idx + 1} did NOT meet statistical significance."
            )
            print(f"[INFO] Mass Group {idx + 1} classified as mass_only_group.")
            if mass_only_group:
                mass_only_groups.append(
                    pd.DataFrame(mass_only_group, columns=["m/z", "CCS"])
                )
            else:
                print(f"[DEBUG] Mass Group {idx + 1} is empty after analysis.")

    # Convert lists of DataFrames into single DataFrames
    if IM_groups:
        IM_groups_df = pd.concat(IM_groups, ignore_index=True)
    else:
        IM_groups_df = pd.DataFrame(columns=["m/z", "CCS"])

    if mass_only_groups:
        mass_only_groups_df = pd.concat(mass_only_groups, ignore_index=True)
    else:
        mass_only_groups_df = pd.DataFrame(columns=["m/z", "CCS"])

    # Print final classification results


if __name__ == "__main__":
    main()
