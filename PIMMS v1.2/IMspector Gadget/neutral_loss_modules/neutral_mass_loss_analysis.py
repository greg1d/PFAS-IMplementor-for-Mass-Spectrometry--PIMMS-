import os
import sys

import numpy as np
import pandas as pd

# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)
from rt_v_mz_library_search_modules.rt_v_mz_library_searcher import (
    add_back_in_sample_intensities,
)


def drift_time_tolerance_calculation(
    DT, IM_resolving_power=60, IM_tolerance_coefficent=3
):
    """
    Calculates the drift time tolerance based on the IM resolving power.

    Args:
        dt (float): Drift time value.
        IM_resolving_power (int): IM resolving power (default: 60).

    Returns:
        float: Drift time tolerance.
    """
    dt_threshold = (DT / IM_resolving_power) * IM_tolerance_coefficent
    return dt_threshold


def neutral_loss_analysis(adjusted_df, mass_error_ppm=10, neutral_loss_units=None):
    """
    Identifies neutral loss trends and allows multiple neutral losses per group.
    Labels the highest m/z point as "M" and subsequent points as "M-neutral loss".

    Args:
        adjusted_df (pd.DataFrame): Input dataset with m/z values.
        mass_error_ppm (int): PPM error tolerance for matching.
        neutral_loss_units (dict): Dictionary of user-defined neutral loss units.

    Returns:
        pd.DataFrame: DataFrame containing identified neutral loss groups.
    """
    adjusted_df = adjusted_df.sort_values(by="m/z", ascending=False).reset_index(
        drop=True
    )
    neutral_loss_groups = []

    required_columns = {
        "m/z",
        "RT",
        "DT",
        "ID",
        "CCS",
        "Classification Type",
        "Match Source",
        "Match",
    }
    if not required_columns.issubset(adjusted_df.columns):
        raise ValueError(
            f"CSV file must contain the following columns: {required_columns}"
        )

    if neutral_loss_units is None:
        neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}

    # Define specific mass differences for multiple adduct losses
    multi_loss_units = {
        "2CO2": (87, 89),
        "CO2-SO3": (123, 125),
        "2SO3": (159, 161),
    }

    group_counter = 0
    processed_indices = set()

    for i in range(len(adjusted_df)):
        if i in processed_indices:
            continue

        mz_value = adjusted_df.at[i, "m/z"]
        group_counter += 1

        current_group = [
            {
                "GroupID": group_counter,
                "m/z": mz_value,
                "RT": adjusted_df.at[i, "RT"],
                "DT": adjusted_df.at[i, "DT"],
                "ID": adjusted_df.at[i, "ID"],
                "CCS": adjusted_df.at[i, "CCS"],
                "Classification Type": adjusted_df.at[i, "Classification Type"],
                "Match Source": adjusted_df.at[i, "Match Source"],
                "Match": adjusted_df.at[i, "Match"],
                "Neutral Loss": "M",
            }
        ]
        processed_indices.add(i)

        search_queue = [i]

        while search_queue:
            current_idx = search_queue.pop(0)
            current_mz = adjusted_df.at[current_idx, "m/z"]

            for j in range(
                len(adjusted_df)
            ):  # Compare ALL peaks, including those already added
                if j == current_idx or j in processed_indices:
                    continue

                next_mz_value = adjusted_df.at[j, "m/z"]
                mass_diff = abs(current_mz - next_mz_value)
                ppm_tolerance = (mass_error_ppm / 1e6) * (current_mz + next_mz_value)
                neutral_loss_labels = []  # Track multiple matches

                for unit_name, M in neutral_loss_units.items():
                    mass_separation = abs(mass_diff - M)
                    if mass_separation <= ppm_tolerance:
                        neutral_loss_labels.append(
                            f"M-{unit_name}"
                        )  # Store all matches

                if neutral_loss_labels:  # If multiple matches exist
                    current_group.append(
                        {
                            "GroupID": group_counter,
                            "m/z": next_mz_value,
                            "RT": adjusted_df.at[j, "RT"],
                            "DT": adjusted_df.at[j, "DT"],
                            "ID": adjusted_df.at[j, "ID"],
                            "CCS": adjusted_df.at[j, "CCS"],
                            "Classification Type": adjusted_df.at[
                                j, "Classification Type"
                            ],
                            "Match Source": adjusted_df.at[j, "Match Source"],
                            "Match": adjusted_df.at[j, "Match"],
                            "Neutral Loss": ", ".join(
                                neutral_loss_labels
                            ),  # Store multiple neutral losses
                        }
                    )
                    processed_indices.add(j)
                    search_queue.append(j)  # Continue checking the new match

        highest_mz = max(entry["m/z"] for entry in current_group)  # Identify M peak

        for entry in current_group:
            secondary_mass_diff = abs(highest_mz - entry["m/z"])

            # ✅ If within 0.1 Da of M, reassign as "M"
            if secondary_mass_diff <= 0.1:
                entry["Neutral Loss"] = "M"

            # ✅ Otherwise, check multi-adduct losses
            elif entry["Neutral Loss"] != "M":  # Only modify non-M peaks
                for unit_name, (lower_bound, upper_bound) in multi_loss_units.items():
                    if lower_bound <= secondary_mass_diff <= upper_bound:
                        entry["Neutral Loss"] = f"M-{unit_name}"  # Update label

        if len(current_group) > 1:
            neutral_loss_groups.extend(current_group)

    result_df = pd.DataFrame(neutral_loss_groups)

    return result_df


def filter_multiple_carboxylic_acids(
    result_df,
    mass_error_ppm=10,
    IM_resolving_power=60,
    IM_tolerance_coefficient=5,
    rt_threshold=1.0,
):
    """
    Identifies alignment of M-SO3 relative to M or M-8 based on mass and DT/RT.

    Args:
        result_df (pd.DataFrame): DataFrame containing neutral loss groups.
        mass_diff_m8 (float): Expected mass difference for M-8 (default: 8.022843).
        mass_diff_so3 (float): Expected mass difference for M-SO3 (default: 79.956817).
        mass_error_ppm (int): The PPM error tolerance for matching.
        IM_resolving_power (int): IM resolving power (default: 60).
        IM_tolerance_coefficient (int): Scaling coefficient for tolerance (default: 3).
        rt_threshold (float): RT range threshold in minutes.
        comparison_type (str): 'both', 'either', 'DT', 'RT', or 'none'.

    Returns:
        pd.DataFrame: DataFrame containing only the M, M-8, and M-SO3 peaks with alignment results.
    """

    if result_df.empty:
        print("[WARNING] No groups found in result_df. Returning empty DataFrame.")
        return result_df

    unique_groups = result_df["GroupID"].unique()
    updated_groups = []
    new_m8_groups = []
    mass_diff_m8 = 8.022843
    mass_diff_so3 = 79.956817
    for group_id in unique_groups:
        group = result_df[result_df["GroupID"] == group_id].copy()
        mz_values = group["m/z"].values

        m_peak, m8_peak, so3_peak = None, None, None
        m_row, m8_row, so3_row = None, None, None  # Store rows for subgroup

        # ✅ Find the M peak (highest m/z in the group)
        m_peak = mz_values.max()
        m_row = group[group["m/z"] == m_peak].iloc[0]

        # ✅ Find the M-8 peak
        for _, row in group.iterrows():
            mass_diff = abs(m_peak - row["m/z"])
            ppm_tolerance = (mass_error_ppm / 1e6) * (m_peak + row["m/z"])
            if abs(mass_diff - mass_diff_m8) <= ppm_tolerance:
                m8_peak = row["m/z"]
                m8_row = row
                break

                # ✅ Find the M-SO3 peak
        for _, row in group.iterrows():
            if m8_peak is None:
                break  # Skip processing if no M-8 peak exists

            mass_diff = abs(m8_peak - row["m/z"])
            ppm_tolerance = (mass_error_ppm / 1e6) * (m_peak + row["m/z"])

            if abs(mass_diff - mass_diff_so3) <= ppm_tolerance:
                so3_peak = row["m/z"]
                so3_row = row
                break

        if m8_peak and so3_peak:
            # **Step 2: Check DT & RT Alignment within the subgroup**
            dt_m = m_row["DT"]
            dt_m8 = m8_row["DT"]
            dt_so3 = so3_row["DT"]

            rt_m = m_row["RT"]
            rt_m8 = m8_row["RT"]
            rt_so3 = so3_row["RT"]

            # ✅ Compute DT threshold dynamically
            median_dt = np.median([dt_m, dt_m8, dt_so3])
            dt_threshold = (median_dt / IM_resolving_power) * IM_tolerance_coefficient

            # ✅ Compute absolute differences
            dt_m_diff = abs(dt_so3 - dt_m)
            dt_m8_diff = abs(dt_so3 - dt_m8)

            rt_m_diff = abs(rt_so3 - rt_m)
            rt_m8_diff = abs(rt_so3 - rt_m8)

            dt_m_valid = dt_m_diff <= dt_threshold
            dt_m8_valid = dt_m8_diff <= dt_threshold

            rt_m_valid = rt_m_diff <= rt_threshold
            rt_m8_valid = rt_m8_diff <= rt_threshold

            # ✅ Determine reassignment of SO₃
            if dt_m8_valid and rt_m8_valid:
                so3_row["GroupID"] = f"{group_id}_M8"
                m8_row["GroupID"] = f"{group_id}_M8"
                new_m8_groups.append(
                    pd.DataFrame([m8_row, so3_row])
                )  # Store new M-8 group
                group = group[group["m/z"] != m8_peak]
                group = group[group["m/z"] != so3_peak]
            elif dt_m_valid and rt_m_valid:
                so3_row["GroupID"] = group_id
            elif dt_m8_valid or rt_m8_valid:
                so3_row["GroupID"] = f"{group_id + 10000}"
                m8_row["GroupID"] = f"{group_id + 10000}"
                new_m8_groups.append(pd.DataFrame([m8_row, so3_row]))

                group = group[group["m/z"] != m8_peak]
                group = group[group["m/z"] != so3_peak]
            elif dt_m_valid or rt_m_valid:
                so3_row["GroupID"] = group_id

            else:
                group = group[group["m/z"] != m8_peak]
                group = group[group["m/z"] != so3_peak]

        updated_groups.append(group)

    final_df = (
        pd.concat(updated_groups, ignore_index=True)
        if updated_groups
        else pd.DataFrame()
    )
    m8_group_df = (
        pd.concat(new_m8_groups, ignore_index=True) if new_m8_groups else pd.DataFrame()
    )
    if final_df.empty:
        print("[INFO] No groups matched the specified alignment condition.")
    return final_df, m8_group_df


def reanalyze_neutral_loss_and_handle_exclusions(
    final_df, m8_group_df, mass_error_ppm=10, neutral_loss_units=None
):
    """
    Re-performs neutral loss analysis on the updated groups.
    - Any points excluded from neutral loss grouping are added to the M-8 group.
    - Adds 10,000 to the GroupID of excluded points to move them to the M-8 group.

    Args:
        final_df (pd.DataFrame): The DataFrame containing the reassigned M/M-8 groups.
        m8_group_df (pd.DataFrame): The M-8 assigned groups.
        mass_error_ppm (int): PPM error tolerance for matching.
        neutral_loss_units (dict): Dictionary of user-defined neutral loss units.

    Returns:
        pd.DataFrame: Final DataFrame with reanalyzed neutral loss groups and M-8 reassigned.
    """

    # ✅ Step 1: Run Neutral Loss Analysis on the Updated Groups
    reanalyzed_neutral_loss_df = neutral_loss_analysis(
        final_df, mass_error_ppm=mass_error_ppm, neutral_loss_units=neutral_loss_units
    )

    # ✅ Step 2: Identify Excluded Points
    excluded_points_df = final_df[
        ~final_df["ID"].isin(reanalyzed_neutral_loss_df["ID"])
    ].copy()

    if excluded_points_df.empty:
        return reanalyzed_neutral_loss_df

    # ✅ Step 3: Assign Excluded Points to the M-8 Group
    excluded_points_df["GroupID"] = (
        excluded_points_df["GroupID"].astype(int) + 10000
    )  # Add 10,000 to move to M-8

    # ✅ Step 4: Merge Excluded Points with M-8 Group
    m8_group_df = pd.concat([m8_group_df, excluded_points_df], ignore_index=True)
    # ✅ Step 5: Merge All DataFrames into the Final Output
    final_combined_df = pd.concat(
        [reanalyzed_neutral_loss_df, m8_group_df], ignore_index=True
    )
    return final_combined_df


def filter_neutral_loss_groups(
    final_combined_df,
    IM_resolving_power=60,
    IM_tolerance_coefficient=3,
    rt_threshold=1.0,
    comparison_type="both",
):
    """
    Filters neutral loss groups based on DT and RT range constraints.

    Args:
        neutral_loss_df (pd.DataFrame): DataFrame containing neutral loss groups.
        dt_threshold (float): DT range threshold as a percentage (e.g., 0.05 for 5%).
        rt_threshold (float): RT range threshold in minutes.

    Returns:
        pd.DataFrame: Filtered DataFrame with unwanted groups removed.
    """
    if final_combined_df.empty:
        return final_combined_df  # Return empty DataFrame to prevent further errors.
    valid_types = {"both", "DT", "RT", "none"}
    if comparison_type not in valid_types:
        raise ValueError(f"comparison_type must be one of {valid_types}")

    messy_groups = []
    filtered_groups = []

    unique_groups = final_combined_df["GroupID"].unique()

    for group_id in unique_groups:
        group = final_combined_df[final_combined_df["GroupID"] == group_id].copy()

        median_dt = group["DT"].median()
        median_rt = group["RT"].median()
        dt_threshold = (median_dt / IM_resolving_power) * IM_tolerance_coefficient
        # ✅ Compute absolute deviation of each point from the median
        group["DT_Diff"] = abs(group["DT"] - median_dt)
        group["RT_Diff"] = abs(group["RT"] - median_rt)

        # ✅ Check if group meets filtering criteria using deviation
        dt_exceeds = group["DT_Diff"].max() > dt_threshold
        rt_exceeds = group["RT_Diff"].max() > rt_threshold

        # Apply correct logic based on `comparison_type`
        if comparison_type == "both" and (dt_exceeds or rt_exceeds):
            if len(group) > 2:
                messy_groups.append(group)  # ✅ Mark as a "Messy Group"
                continue
            else:
                continue  # Remove small groups that fail criteria

        elif comparison_type == "either" and (dt_exceeds and rt_exceeds):
            if len(group) > 2:
                messy_groups.append(group)
                continue
            else:
                continue
        elif comparison_type == "RT" and rt_exceeds:
            if len(group) > 2:
                messy_groups.append(group)
                continue
            else:
                continue  # Only RT matters
        elif comparison_type == "DT" and dt_exceeds:
            if len(group) > 2:
                messy_groups.append(group)
                continue
            else:
                continue
        elif comparison_type == "none":
            pass  # Keep everything
        group["Outlier"] = False

        filtered_groups.append(group)

    filtered_df = (
        pd.concat(filtered_groups, ignore_index=True)
        if filtered_groups
        else pd.DataFrame()
    )

    messy_df = (
        pd.concat(messy_groups, ignore_index=True) if messy_groups else pd.DataFrame()
    )
    filtered_df = filtered_df.drop(columns=["DT_Diff", "RT_Diff"], errors="ignore")

    return filtered_df, messy_df


def refine_messy_groups(
    messy_df,
    rt_threshold=1.0,
    comparison_type="both",
    IM_resolving_power=60,
    IM_tolerance_coefficient=3,
):
    """
    Iteratively refines messy groups by marking outliers instead of removing them.
    Adds a new 'Outlier' column where outliers are flagged as True but retained in the dataset.
    Stores outliers separately but does not append them to the final refined group.

    Args:
        messy_df (pd.DataFrame): DataFrame containing messy groups.
        rt_threshold (float): RT range threshold.
        comparison_type (str): 'both', 'either', 'DT', 'RT', or 'none'.
        IM_resolving_power (int): IM resolving power (default: 60).
        IM_tolerance_coefficient (int): Scaling coefficient for tolerance (default: 3).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (Refined DataFrame, Outliers DataFrame)
    """

    if messy_df.empty:
        return messy_df, pd.DataFrame()

    refined_groups = []
    outliers_list = []  # Store outliers separately
    unique_groups = messy_df["GroupID"].unique()

    for group_id in unique_groups:
        group = messy_df[messy_df["GroupID"] == group_id].copy()
        group["Outlier"] = False  # Initialize "Outlier" column

        # ✅ Keep refining until the group meets the threshold OR has <2 points
        while len(group) >= 2:
            # ✅ Compute **dynamic** DT threshold using median DT of this group
            median_dt = group["DT"].median()
            median_rt = group["RT"].median()
            dt_threshold = (median_dt / IM_resolving_power) * IM_tolerance_coefficient

            # ✅ Compute absolute deviation of each point from the median
            group["DT_Diff"] = abs(group["DT"] - median_dt)
            group["RT_Diff"] = abs(group["RT"] - median_rt)

            # ✅ Check if group meets filtering criteria using deviation
            dt_exceeds = group["DT_Diff"].max() > dt_threshold
            rt_exceeds = group["RT_Diff"].max() > rt_threshold

            # ✅ If the group meets the criteria, stop processing
            if (
                (comparison_type == "both" and not (dt_exceeds or rt_exceeds))
                or (comparison_type == "either" and not (dt_exceeds and rt_exceeds))
                or (comparison_type == "DT" and not dt_exceeds)
                or (comparison_type == "RT" and not rt_exceeds)
            ):
                refined_groups.append(group)
                break  # ✅ Exit once the group is fully clean

            # ✅ Identify the worst outlier based on selected comparison type
            if comparison_type == "DT":
                worst_outlier = group.loc[group["DT_Diff"].idxmax()]
            elif comparison_type == "RT":
                worst_outlier = group.loc[group["RT_Diff"].idxmax()]
            elif comparison_type == "both":
                group["DT_Diff"] = abs(group["DT"] - median_dt)
                group["RT_Diff"] = abs(group["RT"] - median_rt)
                worst_outlier = group.loc[
                    group[["DT_Diff", "RT_Diff"]].sum(axis=1).idxmax()
                ]
                group.drop(
                    columns=["DT_Diff", "RT_Diff"], inplace=True, errors="ignore"
                )
            else:
                refined_groups.append(group)
                break  # ✅ Exit loop if invalid comparison type

            worst_outlier["Outlier"] = True  # Mark as outlier
            outliers_list.append(worst_outlier)  # Store outlier separately
            group = group.drop(worst_outlier.name)  # Keep refining without this outlier

        # ✅ If after all removals, no valid group remains, discard it
        if len(group) < 2:
            continue

    # ✅ Convert list of DataFrames into a single DataFrame before returning
    refined_df = (
        pd.concat(refined_groups, ignore_index=True)
        if refined_groups
        else pd.DataFrame()
    )
    outliers_df = (
        pd.concat(outliers_list, axis=1).T if outliers_list else pd.DataFrame()
    )

    refined_df = refined_df.drop_duplicates(subset="ID", keep="first")

    # ✅ Adhere refined_df and outliers_df together
    final_df = pd.concat([refined_df, outliers_df], ignore_index=True)

    # ✅ Remove groups that contain only outliers
    valid_groups = final_df.groupby("GroupID").filter(lambda g: not g["Outlier"].all())
    valid_groups = valid_groups.drop(columns=["DT_Diff", "RT_Diff"], errors="ignore")

    return valid_groups


def combine_filtered_groups(filtered_df, refined_groups, mz_tolerance=10):
    """
    Combines the valid filtered groups and the refined messy groups into a single DataFrame.
    Removes groups where all high m/z points (within mz_tolerance of max m/z) are marked as outliers.

    Args:
        filtered_df (pd.DataFrame or None): The filtered neutral loss groups that passed initial criteria.
        refined_groups (pd.DataFrame or None): The refined messy groups after outlier handling.
        mz_tolerance (float): The range within the highest m/z to consider for exclusion.

    Returns:
        pd.DataFrame: Combined DataFrame containing all valid neutral loss groups.
    """

    # ✅ Ensure inputs are DataFrames, convert None to empty DataFrame
    if filtered_df is None or not isinstance(filtered_df, pd.DataFrame):
        filtered_df = pd.DataFrame()

    if refined_groups is None or not isinstance(refined_groups, pd.DataFrame):
        refined_groups = pd.DataFrame()

    # ✅ Handle case where both DataFrames are empty
    if filtered_df.empty and refined_groups.empty:
        return pd.DataFrame()

    # ✅ Combine both DataFrames into one final neutral loss group
    neutral_loss_groups_after_filtering = pd.concat(
        [filtered_df, refined_groups], ignore_index=True
    )

    # ✅ Identify and remove groups where all high m/z points are outliers
    valid_groups = []
    unique_groups = neutral_loss_groups_after_filtering["GroupID"].unique()

    for group_id in unique_groups:
        group = neutral_loss_groups_after_filtering[
            neutral_loss_groups_after_filtering["GroupID"] == group_id
        ].copy()

        if "Outlier" not in group.columns:
            group["Outlier"] = False  # Ensure outlier column exists

        # ✅ Find the highest m/z value in the group
        max_mz = group["m/z"].max()
        high_mz_points = group[group["m/z"] >= (max_mz - mz_tolerance)]

        # ✅ If all high m/z points are outliers, remove the group
        if high_mz_points["Outlier"].all():
            continue  # Skip this group

        valid_groups.append(group)

    # ✅ Final DataFrame with only valid groups
    final_df = (
        pd.concat(valid_groups, ignore_index=True) if valid_groups else pd.DataFrame()
    )

    return final_df


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)
    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}
    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )

    # ✅ Define shared parameters
    IM_resolving_power = 60
    IM_tolerance_coefficient = 3
    rt_threshold = 1.0
    comparison_type = "both"
    mass_error_ppm = 10

    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss, messy_df = filter_neutral_loss_groups(
        neutral_loss_groups,
        IM_resolving_power,
        IM_tolerance_coefficient,
        rt_threshold,
        comparison_type,
    )

    final_df, m8_group_df = filter_multiple_carboxylic_acids(
        messy_df,
        mass_error_ppm,
        IM_resolving_power,
        IM_tolerance_coefficient,
        rt_threshold,
    )

    final_combined_df = reanalyze_neutral_loss_and_handle_exclusions(
        final_df, m8_group_df, mass_error_ppm=10, neutral_loss_units=None
    )
    post_extended_refinement = refine_messy_groups(
        final_combined_df,
        rt_threshold,
        comparison_type,
        IM_resolving_power,
        IM_tolerance_coefficient,
    )

    neutral_loss_groups_after_filtering = combine_filtered_groups(
        filtered_neutral_loss, post_extended_refinement
    )
    neutral_loss_groups_after_filtering = add_back_in_sample_intensities(
        adjusted_df,
        neutral_loss_groups_after_filtering,
    )
    neutral_loss_groups_after_filtering.to_csv(
        "neutral_loss_groups_after_filtering.csv", index=False
    )


if __name__ == "__main__":
    main()
