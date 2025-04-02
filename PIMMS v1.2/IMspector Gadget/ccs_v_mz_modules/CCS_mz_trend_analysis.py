import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import linregress

# ✅ Define the correct base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # This is ccs_v_mz_modules
IMPECTOR_GADGET_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..")
)  # Move up to IMspector Gadget

# ✅ Ensure Python finds `config.py`
if IMPECTOR_GADGET_DIR not in sys.path:
    sys.path.append(IMPECTOR_GADGET_DIR)  # Add IMspector Gadget to sys.path


def mz_repeating_unit_analysis(
    adjusted_df, selected_repeating_units, mass_error_ppm=10
):
    """
    Identifies homologous series trends by checking different repeating units.
    Ensures unique groups based on ID values while allowing a single peak to appear in multiple homologous series.

    Args:
        adjusted_df (pd.DataFrame): Input dataset with m/z values.
        selected_repeating_units (dict): Dictionary of user-selected repeating units.
        mass_error_ppm (int): PPM error tolerance for matching.

    Returns:
        pd.DataFrame: DataFrame containing identified homologous series.
    """
    print(f"[DEBUG] User-selected repeating units: {selected_repeating_units}")

    if not isinstance(selected_repeating_units, dict):
        print(
            "[ERROR] selected_repeating_units must be a dictionary! Returning blank DataFrame."
        )
        return pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    if not selected_repeating_units:
        print("[WARNING] No repeating units selected. Returning blank DataFrame.")
        return pd.DataFrame(columns=["GroupID", "m/z", "CCS"])

    iteration_count = 0  # Track loop iterations
    group_counter = 0  # Track unique Group ID

    # **Sort data by m/z for efficient searching**
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)

    unique_group_ids = set()
    mass_groups = []

    for unit_name, M in selected_repeating_units.items():
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
                    "RT": adjusted_df.at[i, "RT"],
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
                    ppm_tolerance = (mass_error_ppm / 1e6) * (
                        current_mz + next_mz_value
                    )
                    if any(
                        abs(mass_diff - M * k) <= ppm_tolerance for k in range(1, 3)
                    ):
                        current_group.append(
                            {
                                "GroupID": group_counter,  # Keep same Group ID
                                "m/z": next_mz_value,
                                "ID": adjusted_df.at[j, "ID"],
                                "RT": adjusted_df.at[j, "RT"],
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

    # **Combine all groups into a single DataFrame**
    if mass_groups:
        mass_groups = pd.concat(mass_groups, ignore_index=True)
    else:
        mass_groups = pd.DataFrame(
            columns=[
                "GroupID",
                "m/z",
                "ID",
                "RT",
                "CCS",
                "Classification Type",
                "Match Source",
                "Match",
                "Repeating Unit",
            ]
        )

    print(
        f"[INFO] mz_repeating_unit_analysis completed. Found {len(mass_groups)} entries."
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

    if mass_groups.empty:
        print("[ERROR] Received empty group list. Exiting function.")
        return [], [], [], []

    # Extract m/z and CCS values
    data_points = list(zip(mass_groups["m/z"], mass_groups["CCS"]))
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    # If there are fewer than 3 points, return as mass_only_group
    if len(mz_values) < 3:
        for mz, ccs in data_points:
            pass
        return [], [], [], data_points

    # Perform initial linear regression
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)

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
        pass

    # Recalculate regression after removing flagged points
    mz_values = np.array([p[0] for p in refined_data_points])
    ccs_values = np.array([p[1] for p in refined_data_points])
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)

    # Final classification: if statistically significant, return as IM_group
    if p_value <= significance_cutoff and slope > 0:
        return refined_data_points, post_source_decay, branched_isomer, []

    return (
        [],
        post_source_decay,
        branched_isomer,
    )


def main():
    """Run the analysis pipeline and return results."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, selected_repeating_units={"CF2": 49.9968064}
    )
    if mass_groups.empty:
        return None  # Exit if no groups found
    print("mass groups", mass_groups)
    # Explicitly exclude the 'GroupID' column while applying the function
    return mass_groups.groupby("GroupID", group_keys=False).apply(
        lambda group: CCS_v_mz_analysis(
            group.drop(columns=["GroupID"], errors="ignore")
        )
    )


if __name__ == "__main__":
    results = main()
