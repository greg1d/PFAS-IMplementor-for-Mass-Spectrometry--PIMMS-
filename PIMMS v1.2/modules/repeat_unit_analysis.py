import bisect  # Import the bisect module
import time

import networkx as nx
import pandas as pd
from creating_single_df import stack_library_with_adjusted

# --- This is the full, correct function ---


# Add these imports if they are not already at the top of your module file


def mz_repeating_unit_analysis(
    df, selected_repeating_units, mass_error_ppm=10, min_valid_points=3
):
    """
    Identifies homologous series using a graph-based approach, now dynamically
    preserving all sample columns found in the input DataFrame.
    """
    # --- MODIFIED: Dynamic Column Preservation Logic ---

    # 1. Define all known, non-sample columns that might be in the data.
    known_non_sample_cols = {
        "Name",
        "Classification Type",
        "CCS",
        "RT",
        "m/z",
        "ID",
        "Average Abundance",
        "Detection Frequency (%)",
        "Match Source",
        "Mass Error (ppm)",
        "CCS Error (%)",
        "RT Error (abs)",
        "DT",
        "GroupID",
        "Repeating Unit",  # Also exclude columns created by this function
    }

    # 2. Dynamically identify sample columns by finding what is NOT a known column.
    sample_cols = sorted(
        [col for col in df.columns if col not in known_non_sample_cols]
    )
    if sample_cols:
        print(f"[INFO] Dynamically preserving sample columns: {sample_cols}")

    # 3. Define the base columns we always want in a specific order.
    base_cols = [
        "Name",
        "Classification Type",
        "CCS",
        "RT",
        "m/z",
        "ID",
        "Average Abundance",
        "Detection Frequency (%)",
    ]

    # 4. The final list of columns to keep is the base list + the dynamic sample list.
    cols_to_preserve = [col for col in base_cols if col in df.columns] + sample_cols

    # --- End of Modification ---

    # Ensure placeholder 'Name' column exists if it wasn't in the input
    if "Name" not in df.columns:
        df["Name"] = "Unknown"

    # Check for the absolute minimum columns needed for the algorithm to run
    if not all(col in df.columns for col in ["m/z", "CCS"]):
        print("[ERROR] Missing 'm/z' or 'CCS' columns required for analysis.")
        return pd.DataFrame()

    # The rest of the function's logic for data prep and graph building remains the same
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

    # --- Enhanced graph-building logic (search multiples of repeating unit) ---
    G = nx.Graph()
    G.add_nodes_from(df.index)

    # You can configure how many multiples to check (e.g. up to 5 × CF2)
    MAX_MULTIPLES = 3

    for current_idx in range(len(df)):
        current_mz = df.at[current_idx, "m/z"]

        for unit_name, M in selected_repeating_units.items():
            # Loop over multiples of this repeating unit (1×, 2×, 3×, ...)
            for mult in range(1, MAX_MULTIPLES + 1):
                effective_shift = M * mult
                target_mz = current_mz + effective_shift
                ppm_tolerance = (mass_error_ppm / 1e6) * target_mz

                lower_bound = target_mz - ppm_tolerance
                upper_bound = target_mz + ppm_tolerance

                start_slice = bisect.bisect_left(
                    mz_list, lower_bound, lo=current_idx + 1
                )
                end_slice = bisect.bisect_right(mz_list, upper_bound, lo=start_slice)

                # We use positional slicing rather than index selection to avoid .empty issues
                candidate_positions = list(range(start_slice, end_slice))
                if not candidate_positions:
                    continue

                best_candidate_pos = min(
                    candidate_positions,
                    key=lambda i: abs(df.at[i, "m/z"] - target_mz),
                )

                # Label the edge with both the base unit and its multiple
                G.add_edge(
                    current_idx,
                    best_candidate_pos,
                    unit=f"{unit_name}×{mult}",
                    delta_mass=effective_shift,
                )

    # --- Processing components remains unchanged until the final step in the loop ---
    connected_components = list(nx.connected_components(G))
    all_groups = []
    group_counter = 0

    for component in connected_components:
        # ... (all the filtering logic for min_points, well_spaced_points, etc. is unchanged) ...
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

        # --- MODIFIED: This line now uses the new dynamic list of columns ---
        # It will preserve the 'Name' column AND all identified sample columns.
        final_group = group_df_rows[cols_to_preserve].copy()

        final_group["GroupID"] = int(group_counter)
        final_group["Repeating Unit"] = list(selected_repeating_units.keys())[0]
        all_groups.append(final_group)

    elapsed_time = time.perf_counter() - start_time
    print(f"[INFO] Series identification finished in {elapsed_time:.4f} seconds.")

    if not all_groups:
        print("[INFO] No valid homologous series were found.")
        return pd.DataFrame()

    return pd.concat(all_groups, ignore_index=True)


def mz_group_refinement(mass_groups_df, min_valid_points=3):
    """
    Refines homologous groups by removing non-monotonic points and validates
    groups based on the number of well-spaced points.

    Args:
        mass_groups_df (pd.DataFrame): DataFrame from mz_repeating_unit_analysis.
        min_valid_points (int): Minimum number of well-spaced (m/z >= 10) points
                                required for a group to be valid.

    Returns:
        pd.DataFrame: A refined DataFrame ready for RANSAC analysis.
    """
    if mass_groups_df.empty:
        return mass_groups_df

    print("\n[INFO] Starting pre-RANSAC group refinement...")
    df = mass_groups_df.copy()

    # --- Step 1: Filter individual non-monotonic points (Vectorized) ---
    df.sort_values(by=["GroupID", "m/z"], inplace=True)
    df["prev_m/z"] = df.groupby("GroupID")["m/z"].shift(1)
    df["prev_CCS"] = df.groupby("GroupID")["CCS"].shift(1)
    df["prev_RT"] = df.groupby("GroupID")["RT"].shift(1)

    mz_jump = (df["m/z"] - df["prev_m/z"]) >= 10
    non_monotonic = (df["CCS"] <= df["prev_CCS"]) | (df["RT"] <= df["prev_RT"])
    points_to_drop_mask = mz_jump & non_monotonic

    refined_df = df[~points_to_drop_mask].copy()
    print(f"[INFO] Removed {points_to_drop_mask.sum()} non-monotonic points.")
    refined_df.drop(columns=["prev_m/z", "prev_CCS", "prev_RT"], inplace=True)

    if refined_df.empty:
        return refined_df

    # --- Step 2: Filter entire groups that lack enough well-spaced points ---
    print(
        f"[INFO] Validating groups for at least {min_valid_points} well-spaced points..."
    )

    # Define a standard function to check for well-spaced points.
    def _has_enough_well_spaced_points(group):
        """Checks if a group has enough points spaced by at least 10 m/z."""
        # .diff() calculates the difference between consecutive m/z values.
        # .fillna(10) ensures the first point in each group (which has a diff of NaN) is counted.
        well_spaced_count = (group["m/z"].diff().fillna(10) >= 10).sum()
        return well_spaced_count >= min_valid_points

    # Apply the filter using the named function
    final_refined_df = refined_df.groupby("GroupID").filter(
        _has_enough_well_spaced_points
    )

    print(
        f"[INFO] Pre-refinement complete. {final_refined_df['GroupID'].nunique()} groups are valid for RANSAC."
    )

    return final_refined_df


def validate_ransac_trends(ransac_df, min_well_spaced_points, min_library_points):
    """
    Validates the final trend lines produced by RANSAC analysis.

    This function filters trends based on:
    1. The minimum number of well-spaced (m/z diff >= 10) non-outlier points.
    2. The minimum number of external standard non-outlier points.
    3. A fixed R² threshold (>= 0.90).

    It does not drop points — it only flags entire groups that fail the criteria.
    """

    if ransac_df is None or ransac_df.empty:
        return pd.DataFrame()

    print("\n[INFO] Starting post-RANSAC validation of trend lines...")
    validated_df = ransac_df.copy()
    print("[DEBUG] Initial ransac_df head:\n", validated_df.head())

    # --- Filter 1: Minimum well-spaced points (consider only non-outliers) ---
    if min_well_spaced_points > 0:

        def _mark_well_spaced_failures(group):
            non_outliers = group[group["is_outlier"] == False].sort_values(by="m/z")
            well_spaced_count = (non_outliers["m/z"].diff().fillna(10) >= 10).sum()
            if well_spaced_count < min_well_spaced_points:
                print(
                    f"[DEBUG] trend_group={group['trend_group'].iloc[0]} | "
                    f"well_spaced_count={well_spaced_count} < required={min_well_spaced_points}"
                )
                group["is_outlier"] = True  # mark entire group as outlier trend
            return group

        validated_df = validated_df.groupby("trend_group", group_keys=False).apply(
            _mark_well_spaced_failures
        )

    # --- Filter 2: Minimum external standard points (consider only non-outliers) ---
    if min_library_points > 0:

        def _mark_library_failures(group):
            non_outliers = group[group["is_outlier"] == False]
            standard_count = (
                non_outliers["Classification Type"] == "External Standard"
            ).sum()
            if standard_count < min_library_points:
                print(
                    f"[DEBUG] trend_group={group['trend_group'].iloc[0]} | "
                    f"standard_count={standard_count} < required={min_library_points}"
                )
                group["is_outlier"] = True
            return group

        validated_df = validated_df.groupby("trend_group", group_keys=False).apply(
            _mark_library_failures
        )

    # --- Filter 3: Fixed R-squared threshold ---
    if "r_squared" in validated_df.columns:

        def _mark_low_r2(group):
            if group["r_squared"].iloc[0] < 0.9:
                print(
                    f"[DEBUG] trend_group={group['trend_group'].iloc[0]} | "
                    f"r_squared={group['r_squared'].iloc[0]:.3f} < 0.9"
                )
                group["is_outlier"] = True
            return group

        validated_df = validated_df.groupby("trend_group", group_keys=False).apply(
            _mark_low_r2
        )

    print(f"[INFO] Post-RANSAC validation complete. Total points: {len(validated_df)}")
    if "GroupID" in validated_df.columns:
        validated_df["trend_group"] = validated_df["GroupID"].astype(float)
    if "trend_group" in validated_df.columns:
        validated_df.drop(columns=["trend_group"], inplace=True)
    return validated_df


if __name__ == "__main__":
    adjusted_df = r"PIMMS v1.2\import folder\Dummy test output.csv"
    pfas_library = r"PIMMS v1.2\import folder\Dummy test output_used_library.csv"
    adjusted_df = pd.read_csv(adjusted_df)
    pfas_library = pd.read_csv(pfas_library)
    print(adjusted_df)
    stacked_df = stack_library_with_adjusted(adjusted_df, pfas_library)

    stacked_df.to_csv(r"PIMMS v1.2\data\stacked_output.csv", index=False)
