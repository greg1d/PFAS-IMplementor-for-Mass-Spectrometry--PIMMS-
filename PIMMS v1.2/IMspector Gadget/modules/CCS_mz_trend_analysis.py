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
    Branched isomers: Residuals < 98% of predicted CCS.
    Post source decay: Residuals > 102% of predicted CCS.
    """

    print("\n[DEBUG] Starting CCS_v_mz_analysis function...")

    if mass_groups.empty:
        print("[ERROR] Received empty group list. Exiting function.")
        return [], [], [], []

    # Extract m/z and CCS values
    data_points = list(zip(mass_groups["m/z"], mass_groups["CCS"]))
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    # If there are fewer than 3 points, return as mass_only_group
    if len(mz_values) < 3:
        print(
            "[WARNING] Not enough points to fit a regression model. Returning as mass_only_group."
        )
        print("\n[INFO] Mass-Only Group Contents:")
        for mz, ccs in data_points:
            print(f"  m/z: {mz:.5f}, CCS: {ccs:.5f}")
        return [], [], [], data_points

    # Perform initial linear regression
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    print(
        f"[DEBUG] Initial regression results: slope={slope:.5f}, r_squared={r_squared:.5f}, p_value={p_value:.5f}"
    )

    # Store classified points
    post_source_decay = []
    branched_isomer = []
    refined_data_points = []

    # Calculate residuals for each point
    for mz, ccs in data_points:
        predicted_ccs = slope * mz + intercept
        residual_ratio = (ccs / predicted_ccs) * 100  # Residual as a percentage

        full_point_metadata = (
            mass_groups.loc[mass_groups["m/z"] == mz].iloc[0].to_dict()
        )
        full_point_metadata["Residual"] = residual_ratio  # Store residual

        if residual_ratio < 95:  # Branched Isomer
            full_point_metadata["Classification"] = "Branched Isomer"
            branched_isomer.append(full_point_metadata)

        elif residual_ratio > 105:  # Post Source Decay
            full_point_metadata["Classification"] = "Post Source Decay"
            post_source_decay.append(full_point_metadata)

        else:  # Valid point remains in trendline
            refined_data_points.append((mz, ccs))

    # Print all classified points with residuals
    for point in post_source_decay + branched_isomer:
        print(
            f"[FLAGGED] m/z: {point['m/z']:.5f}, CCS: {point['CCS']:.5f}, "
            f"Classification: {point['Classification']}, Residual: {point['Residual']:.2f}%"
        )

    # If fewer than 3 points remain after filtering, add ALL flagged points to mass-only group
    if len(refined_data_points) < 3:
        print(
            "[WARNING] Not enough valid points remain after filtering. Returning as mass_only_group."
        )

        # Combine flagged points + remaining valid points
        mass_only_groups = (
            post_source_decay
            + branched_isomer
            + [
                {"m/z": mz, "CCS": ccs, "Classification": "Mass-Only"}
                for mz, ccs in refined_data_points
            ]
        )
        print("\n[DEBUG] Mass-Only Group Identified:")
        if mass_only_groups:
            for point in mass_only_groups:
                print(
                    f"  m/z: {point['m/z']:.5f}, CCS: {point['CCS']:.5f}, Classification: {point['Classification']}"
                )
        else:
            print("[ERROR] Mass-Only Group is empty after processing!")
        return [], post_source_decay, branched_isomer, mass_only_groups

    # Recalculate regression after removing flagged points
    mz_values = np.array([p[0] for p in refined_data_points])
    ccs_values = np.array([p[1] for p in refined_data_points])
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    print(
        f"[DEBUG] Refined regression results: slope={slope:.5f}, r_squared={r_squared:.5f}, p_value={p_value:.5f}"
    )

    # Final classification: if statistically significant, return as IM_group
    if p_value <= significance_cutoff and slope > 0:
        print(
            f"[INFO] Significant positive correlation achieved with {len(refined_data_points)} points. Returning as IM_group."
        )
        return refined_data_points, post_source_decay, branched_isomer, []

    # Otherwise, return everything as mass_only_group
    print(
        "[WARNING] No statistically significant trend found. Returning as mass_only_group."
    )

    # Combine flagged points + remaining valid points
    mass_only_groups = (
        post_source_decay
        + branched_isomer
        + [
            {"m/z": mz, "CCS": ccs, "Classification": "Mass-Only"}
            for mz, ccs in refined_data_points
        ]
    )

    # Print the full mass-only group
    print("\n[INFO] Mass-Only Group Contents:")
    for point in mass_only_groups:
        print(
            f"  m/z: {point['m/z']:.5f}, CCS: {point['CCS']:.5f}, Classification: {point['Classification']}"
        )

    return [], post_source_decay, branched_isomer, mass_only_groups


def main():
    """Run the analysis pipeline and return results."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)
    repeating_units = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]

    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )
    if mass_groups.empty:
        return None  # Exit if no groups found

    # Explicitly exclude the 'GroupID' column while applying the function
    return mass_groups.groupby("GroupID", group_keys=False).apply(
        lambda group: CCS_v_mz_analysis(
            group.drop(columns=["GroupID"], errors="ignore")
        )
    )


if __name__ == "__main__":
    results = main()
