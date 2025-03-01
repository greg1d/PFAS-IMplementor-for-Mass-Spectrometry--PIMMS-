import pandas as pd


def neutral_loss_analysis(adjusted_df, mass_error_ppm=10, neutral_loss_units=None):
    """
    Identifies neutral loss trends by checking different neutral loss units.
    Ensures unique groups based on ID values while allowing a single peak to appear in multiple homologous series.

    Args:
        adjusted_df (pd.DataFrame): Input dataset with m/z values.
        mass_error_ppm (int): PPM error tolerance for matching.
        neutral_loss_units (dict): Dictionary of user-defined neutral loss units.

    Returns:
        pd.DataFrame: DataFrame containing identified neutral loss groups.
    """
    # Sort data by m/z for efficient searching
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)
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
                "Neutral Loss": "None",
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
                        matching_unit = unit_name
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
                            "Neutral Loss": matching_unit,  # Assign the matched unit
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


def main():
    # Example usage
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    neutral_loss_units = {"SO3": 79.956817, "CO2": 43.98983}
    neutral_loss_groups = neutral_loss_analysis(
        adjusted_df, mass_error_ppm=10, neutral_loss_units=neutral_loss_units
    )
    print(neutral_loss_groups)

    # Uncomment to save results
    # neutral_loss_groups.to_csv("neutral_loss_results.csv", index=False)


if __name__ == "__main__":
    main()
