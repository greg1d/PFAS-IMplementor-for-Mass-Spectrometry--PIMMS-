import bisect  # Import the bisect module
import time

import networkx as nx  # You may need to install this: pip install networkx
import pandas as pd
from creating_single_df import stack_library_with_adjusted

# --- This is the full, correct function ---


def mz_repeating_unit_analysis(
    df, selected_repeating_units, mass_error_ppm=10, min_valid_points=3
):
    """
    Identifies homologous series using a graph-based approach.

    Args:
        df (pd.DataFrame): Input data.
        selected_repeating_units (dict): Dictionary of repeating units.
        mass_error_ppm (int): Mass error tolerance.
        min_valid_points (int): The minimum number of well-spaced points required
                                to form a valid homologous series.
    """
    required_cols = ["Name", "Classification Type", "CCS", "RT", "m/z", "ID"]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        print(f"[ERROR] Missing required columns for analysis: {missing}")
        return pd.DataFrame()

    for col in ["m/z", "CCS", "RT", "ID"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["m/z", "CCS"], inplace=True)
    df = df.sort_values(by="m/z").reset_index(drop=True)
    mz_list = df["m/z"].tolist()

    print(f"[INFO] Starting graph-based series search on {len(df)} records...")
    print(
        f"[INFO] A valid series must have at least {min_valid_points} well-spaced points."
    )
    start_time = time.perf_counter()

    G = nx.Graph()
    G.add_nodes_from(df.index)

    for current_idx in range(len(df)):
        current_mz = df.at[current_idx, "m/z"]
        for unit_name, M in selected_repeating_units.items():
            target_mz = current_mz + M
            ppm_tolerance = (mass_error_ppm / 1e6) * target_mz
            lower_bound = target_mz - ppm_tolerance
            upper_bound = target_mz + ppm_tolerance
            start_slice = bisect.bisect_left(mz_list, lower_bound, lo=current_idx + 1)
            end_slice = bisect.bisect_right(mz_list, upper_bound, lo=start_slice)
            candidate_indices = df.index[start_slice:end_slice]
            if not candidate_indices.empty:
                best_candidate_idx = (
                    (df.loc[candidate_indices, "m/z"] - target_mz).abs().idxmin()
                )
                G.add_edge(current_idx, best_candidate_idx, unit=unit_name)

    connected_components = list(nx.connected_components(G))
    all_groups = []
    group_counter = 0

    for component in connected_components:
        if len(component) < min_valid_points:
            continue

        group_indices = list(component)
        group_df_rows = df.loc[group_indices]
        mz_values = group_df_rows["m/z"].tolist()

        unique_sorted_mz = sorted(list(set(mz_values)))
        valid_points_count = 0
        if len(unique_sorted_mz) > 0:
            valid_points_count = 1
            last_counted_mz = unique_sorted_mz[0]
            for mz in unique_sorted_mz[1:]:
                if mz - last_counted_mz >= 10:
                    valid_points_count += 1
                    last_counted_mz = mz

        if valid_points_count < min_valid_points:
            continue

        if not (group_df_rows["Classification Type"] != "External Standard").any():
            continue

        group_counter += 1
        final_group = group_df_rows[required_cols].copy()
        final_group["GroupID"] = group_counter
        final_group["Repeating Unit"] = list(selected_repeating_units.keys())[0]
        all_groups.append(final_group)

    elapsed_time = time.perf_counter() - start_time
    print(f"[INFO] Series identification finished in {elapsed_time:.4f} seconds.")

    if not all_groups:
        print("[INFO] No valid homologous series were found.")
        return pd.DataFrame()

    return pd.concat(all_groups, ignore_index=True)


def mz_group_refinement(mass_groups_df, min_library_points=0, min_valid_points=3):
    """
    Refines groups by removing non-trending points and then validates groups
    based on size, spacing, and the minimum number of library points.

    Args:
        mass_groups_df (pd.DataFrame): The DataFrame from mz_repeating_unit_analysis.
        min_library_points (int): The minimum number of points with Classification Type
                                  'External Standard' required for a group to be valid.
    """
    if mass_groups_df.empty:
        return mass_groups_df

    print("\n[INFO] Starting group refinement process...")
    print(
        f"[INFO] A valid group must contain at least {min_library_points} 'External Standard' points."
    )

    indices_to_drop = []
    for group_id, group in mass_groups_df.groupby("GroupID"):
        group = group.sort_values(by="m/z")
        for i in range(1, len(group)):
            current_point = group.iloc[i]
            previous_point = group.iloc[i - 1]
            if current_point["m/z"] - previous_point["m/z"] >= 10:
                if not (
                    current_point["CCS"] > previous_point["CCS"]
                    and current_point["RT"] > previous_point["RT"]
                ):
                    indices_to_drop.append(current_point.name)

    refined_df = mass_groups_df.drop(indices_to_drop)

    if refined_df.empty:
        print("[INFO] Refinement complete. No groups remain after trend filtering.")
        return refined_df

    print("[INFO] Validating groups for size, spacing, and library point count...")
    valid_group_ids = []
    for group_id, group in refined_df.groupby("GroupID"):
        # Check 1: Validate size and spacing
        mz_values = group["m/z"].tolist()
        unique_sorted_mz = sorted(list(set(mz_values)))
        valid_points_count = 0
        if len(unique_sorted_mz) > 0:
            valid_points_count = 1
            last_counted_mz = unique_sorted_mz[0]
            for mz in unique_sorted_mz[1:]:
                if mz - last_counted_mz >= 10:
                    valid_points_count += 1
                    last_counted_mz = mz

        if valid_points_count < min_valid_points:
            print(
                f"\n--- Discarding Group {group_id} (Reason: Fewer than {min_valid_points} well-spaced points) ---"
            )
            print(group)
            continue  # Skip to the next group

        # --- NEW: Check 2: Validate minimum number of library points ---
        library_points_count = (
            group["Classification Type"] == "External Standard"
        ).sum()

        if library_points_count >= min_library_points:
            valid_group_ids.append(group_id)  # Group is valid
        else:
            print(
                f"\n--- Discarding Group {group_id} (Reason: Has {library_points_count} library points, requires {min_library_points}) ---"
            )
            print(group)

    fully_refined_df = refined_df[refined_df["GroupID"].isin(valid_group_ids)].copy()

    print(
        f"\n[INFO] Post-refinement validation complete. {len(valid_group_ids)} groups remain."
    )
    return fully_refined_df


if __name__ == "__main__":
    adjusted_df = r"PIMMS v1.2\import folder\Dummy test output.csv"
    pfas_library = r"PIMMS v1.2\import folder\Dummy test output_used_library.csv"
    adjusted_df = pd.read_csv(adjusted_df)
    pfas_library = pd.read_csv(pfas_library)
    print(adjusted_df)
    stacked_df = stack_library_with_adjusted(adjusted_df, pfas_library)
    selected_repeating_units = {
        "CF2": 49.9968,
    }
    mass_groups = mz_repeating_unit_analysis(
        stacked_df, selected_repeating_units, mass_error_ppm=10
    )

    mass_groups = mz_group_refinement(
        mass_groups, min_library_points=2, min_valid_points=4
    )
    print(mass_groups)
