import pandas as pd
import os
import sys


# ✅ Ensure Python Can Find Modules
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_dir)

from ccs_v_mz_library_search_modules.library_search_module import (
    get_library_path,
    stack_library_with_adjusted,
)

# ✅ Use dynamically selected library path
LIBRARY_PATH = get_library_path()
LIBRARY_MATCH_SOURCE = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]


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
    neutral_loss_df, dt_threshold=0.05, rt_threshold=1.0, comparison_type="both"
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

    filtered_groups = []

    unique_groups = neutral_loss_df["GroupID"].unique()

    for group_id in unique_groups:
        group = neutral_loss_df[neutral_loss_df["GroupID"] == group_id].copy()

        dt_range = (group["DT"].max() - group["DT"].min()) / group["DT"].min()
        rt_range = group["RT"].max() - group["RT"].min()
        dt_exceeds = dt_range > dt_threshold
        rt_exceeds = rt_range > rt_threshold

        # Apply correct logic based on `comparison_type`
        if comparison_type == "both":
            if dt_exceeds or rt_exceeds:
                continue  # Remove entire group
        elif comparison_type == "DT":
            if dt_exceeds:
                continue  # Only DT matters
        elif comparison_type == "RT":
            if rt_exceeds:
                continue  # Only RT matters
        elif comparison_type == "none":
            pass  # Keep everything

        filtered_groups.append(group)

    final_df = (
        pd.concat(filtered_groups, ignore_index=True)
        if filtered_groups
        else pd.DataFrame()
    )

    print(f"[INFO] Filtering complete. Retained {len(final_df)} entries.")
    return final_df


def main():
    # Example usage
    stacked_df = stack_library_with_adjusted()

    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}

    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        stacked_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )
    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss = filter_neutral_loss_groups(
        neutral_loss_groups, dt_threshold=0.1, rt_threshold=1, comparison_type="RT"
    )
    print("[INFO] Filtered neutral loss groups:\n", filtered_neutral_loss)


if __name__ == "__main__":
    main()
