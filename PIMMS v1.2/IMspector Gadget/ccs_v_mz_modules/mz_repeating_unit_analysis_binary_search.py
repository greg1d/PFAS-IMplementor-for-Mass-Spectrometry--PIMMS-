import pandas as pd


def mz_repeating_unit_analysis(
    adjusted_df, selected_repeating_units, mass_error_ppm=10
):
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)
    processed_indices = set()
    group_counter = 0
    mass_groups = []

    for start_idx in range(len(adjusted_df)):
        if start_idx in processed_indices:
            continue
        current_idx = start_idx
        current_mz = adjusted_df.at[current_idx, "m/z"]
        repeating_unit = None  # Initialize repeating_unit to None

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
                "Repeating Unit": "None",  # Initial starting point
            }
        ]
        processed_indices.add(current_idx)
        while True:
            found_next = False
            for unit_name, M in selected_repeating_units.items():
                for k in range(1, 4):  # Check k=1, then k=2, then k=3
                    target_mz = current_mz + k * M
                    ppm_tolerance = (mass_error_ppm / 1e6) * target_mz
                    lower_bound = target_mz - ppm_tolerance
                    upper_bound = target_mz + ppm_tolerance

                    # Find candidates within the range
                    candidate_df = adjusted_df[
                        (~adjusted_df.index.isin(processed_indices))
                        & (adjusted_df["m/z"] >= lower_bound)
                        & (adjusted_df["m/z"] <= upper_bound)
                    ]

                    if not candidate_df.empty:
                        for (
                            candidate_idx
                        ) in candidate_df.index:  # Loop through all valid candidates
                            candidate_mz = adjusted_df.at[candidate_idx, "m/z"]

                            repeating_unit = unit_name

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

                            # Update current position and m/z for next iteration
                            current_mz = adjusted_df.at[candidate_idx, "m/z"]
                            found_next = True

                        # Restart from k=1 after processing a candidate
                        if found_next:
                            break

                if found_next:
                    break

            if not found_next:
                break  # No further matches found, end this group
        # Update the first point's repeating unit to match the rest of the group
        for entry in current_group:
            entry["Repeating Unit"] = repeating_unit

        # Only save groups with at least 3 points and min-max mz difference ≥ 10
        if len(current_group) >= 3:
            mz_values = [entry["m/z"] for entry in current_group]
            if max(mz_values) - min(mz_values) >= 10:
                if group_counter == 0:
                    group_counter = 1  # Start from 1 instead of 0
                else:
                    group_counter += 1
                for entry in current_group:
                    entry["GroupID"] = group_counter

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
