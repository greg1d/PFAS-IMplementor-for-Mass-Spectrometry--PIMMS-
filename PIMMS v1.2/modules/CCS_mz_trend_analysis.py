import matplotlib.pyplot as plt
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
    """Run the full analysis pipeline: Identify homologous series, analyze trends, classify groups, and generate plots."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)
    repeating_units = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]

    print(
        "\n[INFO] Running mz_repeating_unit_analysis to identify homologous series..."
    )
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups were identified.")
        return

    # Storage for classified groups
    IM_groups = []
    mass_only_groups = []
    post_source_decay_groups = []
    branched_isomer_groups = []

    print("\n[INFO] Performing CCS_v_mz_analysis on identified groups...")

    # Treat each mass group independently
    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        print(f"\n[DEBUG] Analyzing Mass Group {idx + 1} (GroupID: {group_id}):")

        # Print the received group before analysis
        print("\n[DEBUG] Received Mass Group for Analysis:")
        print(group_df.to_string(index=False))

        # Perform correlation analysis
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # Store IM Groups with GroupID
        if IM_group:
            print(
                f"[INFO] Mass Group {idx + 1} (GroupID: {group_id}) classified as IM_group."
            )
            im_group_df = pd.DataFrame(IM_group, columns=["m/z", "CCS"])
            im_group_df["GroupID"] = group_id  # Preserve group ID
            IM_groups.append(im_group_df)

        # Store Mass-Only Groups with GroupID
        else:
            print(
                f"[WARNING] Mass Group {idx + 1} (GroupID: {group_id}) did NOT meet statistical significance."
            )
            print(
                f"[INFO] Mass Group {idx + 1} (GroupID: {group_id}) classified as mass_only_group."
            )
            if mass_only_group:
                mass_only_group_df = pd.DataFrame(
                    mass_only_group, columns=["m/z", "CCS"]
                )
                mass_only_group_df["GroupID"] = group_id
                mass_only_groups.append(mass_only_group_df)
            else:
                print(
                    f"[DEBUG] Mass Group {idx + 1} (GroupID: {group_id}) is empty after analysis."
                )

        # Store and print Post Source Decay groups with GroupID
        if post_source_decay:
            post_source_decay_df = pd.DataFrame(post_source_decay)
            post_source_decay_df["GroupID"] = group_id
            post_source_decay_groups.append(post_source_decay_df)
            print(f"\n[INFO] Post Source Decay Identified in Mass Group {idx + 1}:")
            print(post_source_decay_df.to_string(index=False))
            print("-" * 80)

        # Store and print Branched Isomer groups with GroupID
        if branched_isomer:
            branched_isomer_df = pd.DataFrame(branched_isomer)
            branched_isomer_df["GroupID"] = group_id
            branched_isomer_groups.append(branched_isomer_df)
            print(f"\n[INFO] Branched Isomer Identified in Mass Group {idx + 1}:")
            print(branched_isomer_df.to_string(index=False))
            print("-" * 80)

    # Convert lists of DataFrames into single DataFrames, ensuring 'GroupID' is included
    IM_groups_df = (
        pd.concat(IM_groups, ignore_index=True)
        if IM_groups
        else pd.DataFrame(columns=["GroupID", "m/z", "CCS"])
    )
    mass_only_groups_df = (
        pd.concat(mass_only_groups, ignore_index=True)
        if mass_only_groups
        else pd.DataFrame(columns=["GroupID", "m/z", "CCS"])
    )
    post_source_decay_df = (
        pd.concat(post_source_decay_groups, ignore_index=True)
        if post_source_decay_groups
        else pd.DataFrame(columns=["GroupID", "m/z", "CCS", "Classification"])
    )
    branched_isomer_df = (
        pd.concat(branched_isomer_groups, ignore_index=True)
        if branched_isomer_groups
        else pd.DataFrame(columns=["GroupID", "m/z", "CCS", "Classification"])
    )

    # Print final classification results
    print("\n[INFO] Final Classification Results:")
    print(f"  - Identified {len(IM_groups_df)} points in IM_groups")
    print(f"  - Identified {len(mass_only_groups_df)} points in mass_only_groups")
    print(
        f"  - Identified {len(post_source_decay_df)} points in post_source_decay groups"
    )
    print(f"  - Identified {len(branched_isomer_df)} points in branched_isomer groups")

    print("\n[DEBUG] IM_groups DataFrame:")
    print(IM_groups_df.to_string(index=False))

    print("\n[DEBUG] mass_only_groups DataFrame:")
    print(mass_only_groups_df.to_string(index=False))

    print("\n[DEBUG] post_source_decay DataFrame:")
    print(post_source_decay_df.to_string(index=False))

    print("\n[DEBUG] branched_isomer DataFrame:")
    print(branched_isomer_df.to_string(index=False))

    # Plot the mass groups using Matplotlib
    plot_mass_groups(IM_groups_df, mass_only_groups_df)


def plot_mass_groups(IM_groups_df, mass_only_groups_df):
    """Plots mass groups for debugging purposes."""
    plt.figure(figsize=(10, 6))

    # Plot IM Groups
    if not IM_groups_df.empty:
        for group_id, group_df in IM_groups_df.groupby("GroupID"):
            plt.scatter(
                group_df["m/z"],
                group_df["CCS"],
                label=f"IM Group {group_id}",
                alpha=0.7,
            )

    # Plot Mass-Only Groups
    if not mass_only_groups_df.empty:
        for group_id, group_df in mass_only_groups_df.groupby("GroupID"):
            plt.scatter(
                group_df["m/z"],
                group_df["CCS"],
                marker="x",
                label=f"Mass-Only {group_id}",
                alpha=0.7,
            )

    plt.xlabel("m/z")
    plt.ylabel("CCS")
    plt.legend()
    plt.title("Mass Groups Debugging Plot")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
