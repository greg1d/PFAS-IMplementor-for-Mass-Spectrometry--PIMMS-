import os
import sys

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

        if len(current_group) > 1:
            neutral_loss_groups.extend(current_group)
    result_df = pd.DataFrame(neutral_loss_groups)

    return result_df


def filter_neutral_loss_groups(
    neutral_loss_df,
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
    if neutral_loss_df.empty:
        print("[WARNING] No neutral loss groups to filter. Skipping processing.")
        return neutral_loss_df  # Return empty DataFrame to prevent further errors.

    valid_types = {"both", "DT", "RT", "none"}
    if comparison_type not in valid_types:
        raise ValueError(f"comparison_type must be one of {valid_types}")

    messy_groups = []
    filtered_groups = []

    unique_groups = neutral_loss_df["GroupID"].unique()

    for group_id in unique_groups:
        group = neutral_loss_df[neutral_loss_df["GroupID"] == group_id].copy()

        dt_range = (group["DT"].max() - group["DT"].min()) / group["DT"].min()
        rt_range = group["RT"].max() - group["RT"].min()
        median_dt = group["DT"].median()
        dt_threshold = (median_dt / IM_resolving_power) * IM_tolerance_coefficient
        dt_exceeds = dt_range > dt_threshold
        rt_exceeds = rt_range > rt_threshold

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

        filtered_groups.append(group)

    filtered_df = (
        pd.concat(filtered_groups, ignore_index=True)
        if filtered_groups
        else pd.DataFrame()
    )
    messy_df = (
        pd.concat(messy_groups, ignore_index=True) if messy_groups else pd.DataFrame()
    )
    return filtered_df, messy_df


def refine_messy_groups(
    messy_df,
    rt_threshold=1.0,
    comparison_type="both",
    IM_resolving_power=60,
    IM_tolerance_coefficient=3,
):
    """
    Iteratively refines messy groups by removing the point with the greatest absolute difference
    from the median DT (if DT is selected) or the median RT (if RT is selected) until a valid group is formed.

    Args:
        messy_df (pd.DataFrame): DataFrame containing messy groups.
        rt_threshold (float): RT range threshold.
        comparison_type (str): 'both', 'either', 'DT', 'RT', or 'none'.
        IM_resolving_power (int): IM resolving power (default: 60).
        IM_tolerance_coefficient (int): Scaling coefficient for tolerance (default: 3).

    Returns:
        pd.DataFrame: Refined DataFrame with valid groups.
    """

    if messy_df.empty:
        print("[WARNING] No messy groups found. Returning empty DataFrame.")
        return messy_df

    refined_groups = []
    unique_groups = messy_df["GroupID"].unique()

    for group_id in unique_groups:
        group = messy_df[messy_df["GroupID"] == group_id].copy()

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
                group["DT_Diff"] = abs(group["DT"] - median_dt)
                worst_outlier = group.loc[group["DT_Diff"].idxmax()]
                group.drop(columns=["DT_Diff"], inplace=True, errors="ignore")

            elif comparison_type == "RT":
                group["RT_Diff"] = abs(group["RT"] - median_rt)
                worst_outlier = group.loc[group["RT_Diff"].idxmax()]
                group.drop(columns=["RT_Diff"], inplace=True, errors="ignore")

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
                print(
                    f"[WARNING] Invalid comparison_type '{comparison_type}'. Keeping group as is."
                )
                refined_groups.append(group)
                break  # ✅ Exit loop if invalid comparison type

            # ✅ Remove the worst outlier
            print(
                f"[INFO] Removing outlier: {worst_outlier[['m/z', 'DT', 'RT']].to_dict()}"
            )
            group = group.drop(worst_outlier.name)

        # ✅ If after all removals, no valid group remains, discard it
        if len(group) < 2:
            continue

    # ✅ Convert list of DataFrames into a single DataFrame before returning
    if refined_groups:
        refined_df = pd.concat(refined_groups, ignore_index=True)
    else:
        refined_df = (
            pd.DataFrame()
        )  # ✅ Return an empty DataFrame if no valid groups remain

    refined_df = refined_df.drop_duplicates(subset="ID", keep="first")

    return refined_df


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)
    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}
    print("adjusted_df", adjusted_df)
    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )
    neutral_loss_groups = add_back_in_sample_intensities(
        adjusted_df,
        neutral_loss_groups,
    )
    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss, messy_df = filter_neutral_loss_groups(
        neutral_loss_groups,
        IM_resolving_power=60,
        IM_tolerance_coefficient=3,
        rt_threshold=1.0,
        comparison_type="RT",
    )

    post_extended_refinement = refine_messy_groups(
        messy_df,
        rt_threshold=1.0,
        comparison_type="DT",
        IM_resolving_power=60,
        IM_tolerance_coefficient=3,
    )
    print("groups after refine messy groups", post_extended_refinement)


if __name__ == "__main__":
    main()
