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


def filter_adjusted_df(adjusted_df, remove_d_columns=[]):
    """
    Removes specified `.d` columns and filters out rows where all remaining `.d` columns are 0.

    :param adjusted_df: The original DataFrame.
    :param remove_d_columns: List of `.d` column names to remove.
    :return: Filtered DataFrame.
    """
    filtered_df = adjusted_df.copy()

    # **Normalize column names by stripping spaces**
    filtered_df.columns = filtered_df.columns.str.strip()

    # **Update column names in the original DataFrame**
    adjusted_df.columns = adjusted_df.columns.str.strip()  # Strip spaces in-place

    print(
        f"[DEBUG] Existing Columns in adjusted_df after stripping spaces: {set(filtered_df.columns)}"
    )

    # **Remove selected .d columns**
    found_columns = [col for col in remove_d_columns if col in filtered_df.columns]
    missing_columns = [
        col for col in remove_d_columns if col not in filtered_df.columns
    ]

    # **Warn about missing columns**
    if missing_columns:
        print(
            f"[WARNING] The following columns were NOT found in adjusted_df and will not be removed: {missing_columns}"
        )

    if found_columns:
        print(f"[INFO] Removing columns: {found_columns}")
        filtered_df = filtered_df.drop(columns=found_columns, errors="ignore")

    # **Identify remaining .d.DeMP columns**
    d_columns = [col for col in filtered_df.columns if col.endswith(".d.DeMP")]

    print(f"[DEBUG] Remaining .d.DeMP Columns after filtering: {d_columns}")

    if not d_columns:
        print(
            "[WARNING] No remaining .d columns found after filtering. Returning DataFrame as-is."
        )
        return filtered_df  # No further filtering needed if no .d columns exist

    # **Filter out rows where all remaining .d columns are 0**
    mask = (filtered_df[d_columns] > 0).any(
        axis=1
    )  # Keep rows where at least one .d column is > 0
    rows_removed = len(filtered_df) - len(filtered_df[mask])
    filtered_df = filtered_df[mask]

    print(f"[INFO] Removed {rows_removed} rows where all remaining .d columns were 0.")
    print(f"[INFO] Remaining rows in DataFrame: {len(filtered_df)}")

    return filtered_df


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=[]):
    """Identifies homologous series trends by sequentially checking different repeating units.
    Ensures unique groups based on ID values while allowing a single peak to appear in multiple homologous series.
    """

    start_time = time.time()

    # Convert user-provided repeating units into masses using the REPEATING_UNITS dictionary
    selected_units = {
        unit: REPEATING_UNITS[unit]
        for unit in repeating_units
        if unit in REPEATING_UNITS
    }

    # **Sort data by m/z to ensure proper trend building**
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)

    unique_group_ids = set()  # Stores sets of IDs for unique groups
    mass_groups = []  # List to store final DataFrame groups

    print(f"[DEBUG] Total data points: {len(adjusted_df)}")

    # Iterate over each repeating unit sequentially
    for unit_name, M in selected_units.items():
        print(
            f"\n[INFO] Searching for homologous series with repeating unit: {unit_name} (M = {M:.6f})"
        )

        processed_indices = set()  # Track indices already used in a group for this unit

        for i in range(len(adjusted_df)):  # Iterate over all peaks
            if i in processed_indices:
                continue  # Skip if already assigned to a group for this unit

            mz_value = adjusted_df.iloc[i]["m/z"]
            current_group = [
                {
                    "m/z": mz_value,
                    "ID": adjusted_df.iloc[i]["ID"],
                    "CCS": adjusted_df.iloc[i]["CCS"],
                    "Classification Type": adjusted_df.iloc[i]["Classification Type"],
                    "Match Source": adjusted_df.iloc[i]["Match Source"],
                    "Match": adjusted_df.iloc[i]["Match"],
                    "Repeating Unit": unit_name,  # ✅ Store repeating unit type
                }
            ]
            processed_indices.add(i)

            # **Dynamic Expansion Search**
            search_queue = [i]  # Queue to hold indices to check forward

            while search_queue:
                current_idx = search_queue.pop(0)  # Pop the next index to search from
                current_mz = adjusted_df.iloc[current_idx]["m/z"]

                for j in range(current_idx + 1, len(adjusted_df)):  # Look forward
                    if j in processed_indices:
                        continue

                    next_mz_value = adjusted_df.iloc[j]["m/z"]
                    mass_diff = abs(current_mz - next_mz_value)
                    ppm_tolerance = (
                        mass_error_ppm / 1e6
                    ) * current_mz  # Allow tolerance

                    # **Allow close m/z values within ppm tolerance to be included**
                    if mass_diff <= ppm_tolerance:  # ✅ Include very close values
                        current_group.append(
                            {
                                "m/z": next_mz_value,
                                "ID": adjusted_df.iloc[j]["ID"],
                                "CCS": adjusted_df.iloc[j]["CCS"],
                                "Classification Type": adjusted_df.iloc[j][
                                    "Classification Type"
                                ],
                                "Match Source": adjusted_df.iloc[j]["Match Source"],
                                "Match": adjusted_df.iloc[j]["Match"],
                                "Repeating Unit": unit_name,  # ✅ Store repeating unit type
                            }
                        )
                        processed_indices.add(j)
                        search_queue.append(j)

                    # **Check if the difference matches M or 2M from the latest point**
                    elif any(
                        abs(mass_diff - M * k) <= ppm_tolerance for k in range(1, 3)
                    ):  # ✅ Searches for M, 2M
                        current_group.append(
                            {
                                "m/z": next_mz_value,
                                "ID": adjusted_df.iloc[j]["ID"],
                                "CCS": adjusted_df.iloc[j]["CCS"],
                                "Classification Type": adjusted_df.iloc[j][
                                    "Classification Type"
                                ],
                                "Match Source": adjusted_df.iloc[j]["Match Source"],
                                "Match": adjusted_df.iloc[j]["Match"],
                                "Repeating Unit": unit_name,  # ✅ Store repeating unit type
                            }
                        )
                        processed_indices.add(j)
                        search_queue.append(j)

            # **Ensure the group has at least 2 points and is unique based on ID set**
            if len(current_group) >= 2:
                group_ids = frozenset(
                    entry["ID"] for entry in current_group
                )  # Unique ID set

                if group_ids not in unique_group_ids:  # ✅ Prevent duplicate groups
                    unique_group_ids.add(group_ids)  # Track unique group
                    mass_groups.append(
                        pd.DataFrame(current_group)
                    )  # Store as DataFrame

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )

    # **Debugging: Print each group with repeating unit**
    for idx, group_df in enumerate(mass_groups):
        repeating_unit = group_df["Repeating Unit"].iloc[0]  # Extract repeating unit
        print(
            f"\n[DEBUG] Group {idx + 1} - Homologous Series (Repeating Unit: {repeating_unit}):"
        )
        print(group_df.to_string(index=False))  # Print clean table without row index
        print("-" * 80)  # Separator for readability

    return mass_groups


def CCS_v_mz_analysis(mass_groups, significance_cutoff=0.05):
    """
    Identifies homologous series trends by checking if CCS and m/z values are correlated.
    - Iteratively removes the highest residual point until a statistically significant (p ≤ 0.05) positive correlation is found.
    - Groups are classified as:
        - "IM_group": Points that form a statistically significant correlation.
        - "mass_only_group": Groups where no significant correlation is found.
        - "post_source_decay": Removed points above the regression line.
        - "branched_isomer": Removed points below the regression line.
    """

    print("\n[DEBUG] Starting CCS_v_mz_analysis function...")

    if mass_groups.empty:
        print("[ERROR] Received empty group list. Exiting function.")
        return [], [], [], []

    # Convert to NumPy arrays
    data_points = list(zip(mass_groups["m/z"], mass_groups["CCS"]))
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    print(f"[DEBUG] Total points received: {len(data_points)}")
    print(f"[DEBUG] m/z values: {mz_values}")
    print(f"[DEBUG] CCS values: {ccs_values}")

    if len(mz_values) < 3:
        print(
            "[WARNING] Not enough points to fit a regression model. Returning as mass_only_group."
        )
        return [], [], [], data_points  # Return everything as mass_only_group

    # Step 1: Find best fit for all points initially
    slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    print(
        f"[INFO] Initial Fit - Slope: {slope:.6f}, Intercept: {intercept:.6f}, R²: {r_squared:.6f}, p-value: {p_value:.6f}"
    )

    if p_value <= significance_cutoff and slope > 0:
        print(
            "[INFO] Initial group already meets significance and is positively correlated."
        )
        return (
            data_points,
            [],
            [],
            [],
        )  # IM_group, post_source_decay, branched_isomer, mass_only_group

    # Step 2: Iteratively remove the worst point until significance is met
    remaining_points = data_points.copy()
    post_source_decay = []
    branched_isomer = []

    while len(remaining_points) > 2:
        mz_values = np.array([p[0] for p in remaining_points])
        ccs_values = np.array([p[1] for p in remaining_points])
        slope, intercept, r_value, p_value, _ = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        print(
            f"[DEBUG] Current Fit - Slope: {slope:.6f}, Intercept: {intercept:.6f}, R²: {r_squared:.6f}, p-value: {p_value:.6f}"
        )

        if p_value <= significance_cutoff and slope > 0:
            print(
                f"[INFO] Significant positive correlation achieved with {len(remaining_points)} points."
            )
            return (
                remaining_points,
                post_source_decay,
                branched_isomer,
                [],
            )  # Return as IM_group

        # Identify the worst point to remove (highest residual)
        residuals = [
            abs(ccs - (slope * mz + intercept)) for mz, ccs in remaining_points
        ]
        for i, (mz, ccs) in enumerate(remaining_points):
            print(
                f"[DEBUG] Residual for m/z={mz:.4f}, CCS={ccs:.4f}: {residuals[i]:.6f}"
            )

        max_residual_idx = np.argmax(residuals)
        worst_point = remaining_points.pop(max_residual_idx)

        # Classify removed point
        predicted_ccs = slope * worst_point[0] + intercept
        full_point_metadata = (
            mass_groups.loc[mass_groups["m/z"] == worst_point[0]].iloc[0].to_dict()
        )

        if worst_point[1] > (predicted_ccs):
            full_point_metadata["Classification"] = "Post Source Decay"
            post_source_decay.append(full_point_metadata)

            print(
                f"[FLAGGED] Post Source Decay - Removed m/z={worst_point[0]:.4f}, CCS={worst_point[1]:.4f}"
            )
        else:
            full_point_metadata["Classification"] = "Branched Isomer"
            branched_isomer.append(full_point_metadata)
            print(
                f"[FLAGGED] Branched Isomer - Removed m/z={worst_point[0]:.4f}, CCS={worst_point[1]:.4f}"
            )

    # Step 3: If we exit the loop and still don't have a significant model, return as mass_only_group
    print(
        "[WARNING] Could not achieve a statistically significant positive correlation with at least 3 points."
    )
    return [], [], [], data_points  # Return as mass_only_group


def main():
    """Run the analysis and interactive plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"

    print("[DEBUG] Loading dataset...")
    adjusted_df = pd.read_csv(file_path)

    # Define the repeating units to use
    repeating_units = ["CF2", "OCF2"]

    # Filter to only include valid repeating units
    valid_units = [unit for unit in repeating_units if unit in REPEATING_UNITS]

    if not valid_units:
        print("[ERROR] No valid repeating units selected. Exiting...")
        return

    print(
        f"\n[INFO] Running mz_repeating_unit_analysis with repeating units: {valid_units}"
    )
    mass_groups = mz_repeating_unit_analysis(adjusted_df, repeating_units=valid_units)

    if not mass_groups:
        print("[WARNING] No homologous series found. Exiting...")
        return

    # Debugging output: Print the groups and classify them
    for idx, mass_group in enumerate(mass_groups):
        print(f"\n[DEBUG] Processing Mass Group {idx + 1}:")

        # Perform CCS_v_mz_analysis
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(mass_group)
        )

        if IM_group:
            print(f"\n[INFO] Group {idx + 1} identified as an IM_group:")
            print(pd.DataFrame(IM_group).to_string(index=False))
        else:
            print(f"\n[INFO] Group {idx + 1} remains a Mass_Only group:")
            print(pd.DataFrame(mass_only_group).to_string(index=False))

        print("-" * 80)

        # Print the excluded points (if any)
        if post_source_decay:
            print(f"\n[DEBUG] Post Source Decay for Group {idx + 1}:")
            print(pd.DataFrame(post_source_decay).to_string(index=False))
            print("-" * 80)

        if branched_isomer:
            print(f"\n[DEBUG] Branched Isomer for Group {idx + 1}:")
            print(pd.DataFrame(branched_isomer).to_string(index=False))
            print("-" * 80)


if __name__ == "__main__":
    main()
