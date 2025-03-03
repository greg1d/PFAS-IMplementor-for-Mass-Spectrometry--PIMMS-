import pandas as pd


def neutral_loss_analysis(adjusted_df, mass_error_ppm=10, neutral_loss_units=None):
    """
    Identifies neutral loss trends by checking different neutral loss units.
    Labels the highest m/z point as "M" and subsequent points as "M-neutral loss".

    Args:
        adjusted_df (pd.DataFrame): Input dataset with m/z values.
        mass_error_ppm (int): PPM error tolerance for matching.
        neutral_loss_units (dict): Dictionary of user-defined neutral loss units.

    Returns:
        pd.DataFrame: DataFrame containing identified neutral loss groups.
    """
    # Sort data by m/z for efficient searching
    adjusted_df = adjusted_df.sort_values(by="m/z", ascending=False).reset_index(
        drop=True
    )
    neutral_loss_groups = []

    # Ensure required columns exist
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

    # Define default neutral loss units if not provided
    if neutral_loss_units is None:
        neutral_loss_units = {
            "SO3": 79.956817,
            "CO2": 43.98983,
        }

    print(f"[DEBUG] Selected neutral loss units: {neutral_loss_units}")

    # Initialize tracking variables
    group_counter = 0
    iteration_count = 0
    processed_indices = set()

    for i in range(len(adjusted_df)):
        iteration_count += 1
        if i in processed_indices:
            continue

        mz_value = adjusted_df.at[i, "m/z"]
        group_counter += 1  # Assign new unique GroupID

        # Initialize the group with the highest m/z value, labeled as "M"
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
                "Neutral Loss": "M",  # Label highest point as "M"
            }
        ]
        processed_indices.add(i)

        # Start search queue
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
                ppm_tolerance = (mass_error_ppm / 1e6) * (current_mz + next_mz_value)

                print(
                    f"[DEBUG] current_mz: {current_mz}, next_mz_value: {next_mz_value}"
                )
                print(f"[DEBUG] mass_diff: {mass_diff}, ppm_tolerance: {ppm_tolerance}")

                # Check if any neutral loss unit satisfies the tolerance
                matching_unit = None
                for unit_name, M in neutral_loss_units.items():
                    mass_separation = abs(mass_diff - M)
                    if mass_separation <= ppm_tolerance:
                        matching_unit = f"M-{unit_name}"  # Label as M-neutral loss
                        break  # Exit loop early if a match is found

                if matching_unit:
                    print(f"[INFO] Match found for {matching_unit} at {next_mz_value}")
                    current_group.append(
                        {
                            "GroupID": group_counter,  # Keep same Group ID
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
                            "Neutral Loss": matching_unit,  # Assign "M-neutral loss"
                        }
                    )
                    processed_indices.add(j)
                    search_queue.append(j)

        # Ensure that we store the group if matches were found
        if len(current_group) > 1:
            neutral_loss_groups.extend(current_group)

    print(
        f"[INFO] Neutral loss analysis completed. Found {len(neutral_loss_groups)} entries."
    )
    return pd.DataFrame(neutral_loss_groups)


def filter_neutral_loss_groups(
    neutral_loss_df, dt_threshold=0.05, rt_threshold=1.0, comparison_type="both"
):
    """
    Filters neutral loss groups based on user-defined DT and RT thresholds.

    Args:
        neutral_loss_df (pd.DataFrame): DataFrame containing neutral loss groups.
        dt_threshold (float): DT difference threshold as a percentage (e.g., 0.05 for 5%).
        rt_threshold (float): RT difference threshold in minutes.
        comparison_type (str): 'both', 'either', 'DT', 'RT', or 'none'.

    Returns:
        pd.DataFrame: Filtered DataFrame with unwanted groups removed.
    """
    valid_types = {"both", "either", "DT", "RT", "none"}
    if comparison_type not in valid_types:
        raise ValueError(f"comparison_type must be one of {valid_types}")

    filtered_groups = []

    unique_groups = neutral_loss_df["GroupID"].unique()

    for group_id in unique_groups:
        group = neutral_loss_df[neutral_loss_df["GroupID"] == group_id].copy()

        # Get reference values (first row is 'M')
        reference_dt = group.iloc[0]["DT"]
        reference_rt = group.iloc[0]["RT"]

        # Compute DT and RT conditions for all members
        group["DT_Diff"] = abs(group["DT"] - reference_dt) / reference_dt
        group["RT_Diff"] = abs(group["RT"] - reference_rt)

        dt_condition = group["DT_Diff"] <= dt_threshold
        rt_condition = group["RT_Diff"] <= rt_threshold

        if comparison_type == "both":
            valid_group = dt_condition & rt_condition
        elif comparison_type == "either":
            valid_group = dt_condition | rt_condition
        elif comparison_type == "DT":
            valid_group = dt_condition
        elif comparison_type == "RT":
            valid_group = rt_condition
        elif comparison_type == "none":
            valid_group = True  # Include everything

        if valid_group.any():
            filtered_groups.append(group[valid_group])

    final_df = (
        pd.concat(filtered_groups, ignore_index=True)
        if filtered_groups
        else pd.DataFrame()
    )

    print(
        f"[INFO] Filtering complete. Retained {len(final_df)} entries after applying {comparison_type} filter."
    )
    return final_df


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}

    # Step 1: Identify neutral loss groups (without filtering)
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )
    print("[INFO] Initial neutral loss groups:\n", neutral_loss_groups)

    # Step 2: Apply filtering based on user-defined DT and RT thresholds
    filtered_neutral_loss = filter_neutral_loss_groups(
        neutral_loss_groups, dt_threshold=0.5, rt_threshold=5.0, comparison_type="both"
    )
    print("[INFO] Filtered neutral loss groups:\n", filtered_neutral_loss)


if __name__ == "__main__":
    main()
