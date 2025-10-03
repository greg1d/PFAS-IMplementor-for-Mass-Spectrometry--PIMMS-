from creating_single_df import stack_library_with_adjusted
import pandas as pd
import time


import bisect  # Import the bisect module


def mz_repeating_unit_analysis(stacked_df, selected_repeating_units, mass_error_ppm=10):
    """
    Identifies homologous series trends. A group is valid if it contains at least 3
    points that are each separated by a minimum of 10 m/z units.
    """
    # --- Input Validation and Preparation ---
    required_cols = ["Name", "Classification Type", "CCS", "RT", "m/z", "ID"]
    if not all(col in stacked_df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in stacked_df.columns]
        print(f"[ERROR] Input DataFrame is missing required columns: {missing}")
        return pd.DataFrame()

    for col in ["m/z", "CCS", "RT", "ID"]:
        stacked_df[col] = pd.to_numeric(stacked_df[col], errors="coerce")
    stacked_df.dropna(subset=["m/z", "CCS"], inplace=True)

    stacked_df = stacked_df.sort_values(by="m/z").reset_index(drop=True)
    mz_list = stacked_df["m/z"].tolist()

    # --- Series Identification ---
    processed_indices = set()
    group_counter = 0
    all_groups = []

    print(f"[INFO] Starting homologous series search on {len(stacked_df)} records...")
    start_time = time.perf_counter()

    for start_idx in range(len(stacked_df)):
        if start_idx in processed_indices:
            continue

        group_counter += 1
        current_group = []
        queue = [start_idx]
        group_indices = {start_idx}

        while queue:
            current_idx = queue.pop(0)
            current_group.append(
                {
                    "GroupID": group_counter,
                    "m/z": stacked_df.at[current_idx, "m/z"],
                    "RT": stacked_df.at[current_idx, "RT"],
                    "ID": stacked_df.at[current_idx, "ID"],
                    "CCS": stacked_df.at[current_idx, "CCS"],
                    "Classification Type": stacked_df.at[
                        current_idx, "Classification Type"
                    ],
                    "Name": stacked_df.at[current_idx, "Name"],
                }
            )
            current_mz = stacked_df.at[current_idx, "m/z"]
            for unit_name, M in selected_repeating_units.items():
                for k in range(1, 4):
                    target_mz = current_mz + k * M
                    ppm_tolerance = (mass_error_ppm / 1e6) * target_mz
                    lower_bound = target_mz - ppm_tolerance
                    upper_bound = target_mz + ppm_tolerance
                    start_slice = bisect.bisect_left(
                        mz_list, lower_bound, lo=current_idx + 1
                    )
                    end_slice = bisect.bisect_right(
                        mz_list, upper_bound, lo=start_slice
                    )
                    candidate_indices = stacked_df.index[start_slice:end_slice]
                    for cand_idx in candidate_indices:
                        if (
                            cand_idx not in processed_indices
                            and cand_idx not in group_indices
                        ):
                            queue.append(cand_idx)
                            group_indices.add(cand_idx)

        # After exploring all branches, if the group is valid, save it
        mz_values = [entry["m/z"] for entry in current_group]

        # --- NEW, PRECISE VALIDATION LOGIC ---
        unique_sorted_mz = sorted(list(set(mz_values)))

        valid_points_count = 0
        if len(unique_sorted_mz) > 0:
            valid_points_count = 1
            last_counted_mz = unique_sorted_mz[0]
            for mz in unique_sorted_mz[1:]:
                if mz - last_counted_mz >= 10:
                    valid_points_count += 1
                    last_counted_mz = mz

        # Now, check if the count of these well-spaced points is 3 or more.
        if valid_points_count >= 3:
            unit_name_found = list(selected_repeating_units.keys())[0]
            for entry in current_group:
                entry["Repeating Unit"] = unit_name_found
            all_groups.append(pd.DataFrame(current_group))
            processed_indices.update(group_indices)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"[INFO] Series identification loop finished in {elapsed_time:.4f} seconds.")

    if not all_groups:
        print("[INFO] No valid homologous series were found.")
        return pd.DataFrame()

    final_df = pd.concat(all_groups, ignore_index=True)
    return final_df


if __name__ == "__main__":
    adjusted_df = r"PIMMS v1.2\import folder\Dummy test output.csv"
    pfas_library = r"PIMMS v1.2\import folder\Dummy test output_used_library.csv"
    adjusted_df = pd.read_csv(adjusted_df)
    pfas_library = pd.read_csv(pfas_library)
    stacked_df = stack_library_with_adjusted(adjusted_df, pfas_library)
    selected_repeating_units = {
        "CF2": 49.9968,
    }
    mass_groups = mz_repeating_unit_analysis(
        stacked_df, selected_repeating_units, mass_error_ppm=10
    )
    print(mass_groups)
