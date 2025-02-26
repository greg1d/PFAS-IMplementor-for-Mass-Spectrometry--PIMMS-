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
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)
    processed_indices = set()
    group_counter = 0
    mass_groups = []

    print("\n[DEBUG] Sorted adjusted_df:")
    print(adjusted_df)

    for unit_name, M in selected_repeating_units.items():
        for start_idx in range(len(adjusted_df)):
            if start_idx in processed_indices:
                continue
            current_idx = start_idx
            current_mz = adjusted_df.at[current_idx, "m/z"]
            group_counter += 1

            print(
                f"\n[DEBUG] Starting new group: Group {group_counter}, Start m/z = {current_mz:.5f}"
            )

            current_group = [
                {
                    "GroupID": group_counter,
                    "m/z": current_mz,
                    "RT": adjusted_df.at[current_idx, "RT"],
                    "ID": adjusted_df.at[current_idx, "ID"],
                    "CCS": adjusted_df.at[current_idx, "CCS"],
                    "Classification Type": adjusted_df.at[
                        current_idx, "Classification Type"
                    ],
                    "Match Source": adjusted_df.at[current_idx, "Match Source"],
                    "Match": adjusted_df.at[current_idx, "Match"],
                    "Repeating Unit": unit_name,
                }
            ]
            processed_indices.add(current_idx)

            while True:
                found_next = False
                for k in range(1, 4):  # Check k=1, then k=2, then k=3
                    target_mz = current_mz + k * M
                    ppm_tolerance = (mass_error_ppm / 1e6) * target_mz
                    lower_bound = target_mz - ppm_tolerance
                    upper_bound = target_mz + ppm_tolerance

                    print(
                        f"[DEBUG] k={k}, Target m/z={target_mz:.5f}, "
                        f"Lower bound={lower_bound:.5f}, Upper bound={upper_bound:.5f}"
                    )

                    # Find candidates within the range
                    candidate_df = adjusted_df[
                        (~adjusted_df.index.isin(processed_indices))
                        & (adjusted_df["m/z"] >= lower_bound)
                        & (adjusted_df["m/z"] <= upper_bound)
                    ]

                    print(
                        f"[DEBUG] Candidates in range ({lower_bound:.5f}, {upper_bound:.5f}):"
                    )
                    print(candidate_df)

                    if not candidate_df.empty:
                        found_next = True
                        for (
                            candidate_idx
                        ) in candidate_df.index:  # Loop through all valid candidates
                            candidate_mz = adjusted_df.at[candidate_idx, "m/z"]

                            print(
                                f"[MATCH] Found candidate m/z={candidate_mz:.5f} at index {candidate_idx}"
                            )

                            # Append found candidate to current group
                            current_group.append(
                                {
                                    "GroupID": group_counter,
                                    "m/z": candidate_mz,
                                    "RT": adjusted_df.at[candidate_idx, "RT"],
                                    "ID": adjusted_df.at[candidate_idx, "ID"],
                                    "CCS": adjusted_df.at[candidate_idx, "CCS"],
                                    "Classification Type": adjusted_df.at[
                                        candidate_idx, "Classification Type"
                                    ],
                                    "Match Source": adjusted_df.at[
                                        candidate_idx, "Match Source"
                                    ],
                                    "Match": adjusted_df.at[candidate_idx, "Match"],
                                    "Repeating Unit": unit_name,
                                }
                            )

                            processed_indices.add(candidate_idx)  # Mark as processed
                            print(
                                f"[DEBUG] Added to processed_indices: {candidate_idx}"
                            )

                        # Update current position and m/z for next iteration
                        current_idx = max(candidate_df.index)
                        current_mz = adjusted_df.at[current_idx, "m/z"]

                if not found_next:
                    print(
                        f"[DEBUG] No further match found for Group {group_counter}, ending group."
                    )
                    break  # No further matches found, end this group

            # Only save groups with at least 3 points and min-max mz difference ≥ 10
            if len(current_group) >= 3:
                mz_values = [entry["m/z"] for entry in current_group]
                if max(mz_values) - min(mz_values) >= 10:
                    print(
                        f"[DEBUG] Saving valid group {group_counter} with {len(current_group)} points"
                    )
                    mass_groups.append(pd.DataFrame(current_group))

    # Combine groups into a final DataFrame
    if mass_groups:
        mass_groups = pd.concat(mass_groups, ignore_index=True)
    else:
        mass_groups = pd.DataFrame(
            columns=[
                "GroupID",
                "m/z",
                "RT",
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
    r_squared = r_value**2
    print("p value before refinement of the CCS v m/z analysis function: ", p_value)
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

    # If fewer than 3 points remain after filtering, add ALL flagged points to mass-only group
    if len(refined_data_points) < 3:
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
                pass
        else:
            print("[ERROR] Mass-Only Group is empty after processing!")
        return [], post_source_decay, branched_isomer, mass_only_groups

    # Recalculate regression after removing flagged points
    mz_values = np.array([p[0] for p in refined_data_points])
    ccs_values = np.array([p[1] for p in refined_data_points])
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    print("p value after refinement of the CCS v m/z analysis function: ", p_value)
    # Final classification: if statistically significant, return as IM_group
    if p_value <= significance_cutoff and slope > 0:
        return refined_data_points, post_source_decay, branched_isomer, []

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
        pass

    return [], post_source_decay, branched_isomer, mass_only_groups


def main():
    """Run the analysis pipeline and return results."""
    file_path = "stacked_df.csv"
    adjusted_df = pd.read_csv(file_path)
    REPEATING_UNITS = {
        "CF2": 49.9968064,
        "OCF2": 65.9917214,
        "CF2CF2O": 115.988527,
        "CH2CF2": 64.012456,
        "HF": 20.0062278,
    }

    # ✅ Select a subset of repeating units for analysis
    SELECTED_UNITS = ["CF2"]
    selected_repeating_units = {key: REPEATING_UNITS[key] for key in SELECTED_UNITS}
    mass_groups = mz_repeating_unit_analysis(adjusted_df, selected_repeating_units)
    print("mass groups", mass_groups)

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
