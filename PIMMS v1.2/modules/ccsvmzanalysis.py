import pandas as pd


def load_and_combine_data(data_filepath, library_filepath, round_digits=4):
    """
    Reads, cleans, combines, and simplifies experimental data and a reference library.
    Returns a clean DataFrame with only 'm/z', 'CCS', 'Origin', and 'Name'.
    """
    try:
        # 1. Read both files
        adjusted_df = pd.read_csv(data_filepath)
        library_df = pd.read_csv(library_filepath)
        print(
            f"Loaded {len(adjusted_df)} records from data and {len(library_df)} from library."
        )

        # 2. Clean 'm/z' column in both dataframes
        for df, name in [(adjusted_df, "data"), (library_df, "library")]:
            if "m/z" not in df.columns:
                print(f"ERROR: 'm/z' column not found in {name} file.")
                return None
            df["m/z"] = pd.to_numeric(df["m/z"], errors="coerce")
            df.dropna(subset=["m/z"], inplace=True)

        # 3. Create a temporary, rounded 'm/z' column for joining
        adjusted_df["join_mz"] = adjusted_df["m/z"].round(round_digits)
        library_df["join_mz"] = library_df["m/z"].round(round_digits)

        # 4. Perform an OUTER merge to keep all rows from both files
        combined_df = pd.merge(
            adjusted_df,
            library_df,
            on="join_mz",
            how="outer",
            suffixes=("_sample", "_library"),
            indicator=True,
        )

        # 5. Create the 'Origin' column from the merge indicator
        origin_map = {
            "left_only": "sample feature",
            "right_only": "Level 2 library",
            "both": "Matched (Sample and Library)",
        }
        combined_df["Origin"] = combined_df["_merge"].map(origin_map)

        # 6. Create the final, consolidated columns
        # Consolidate m/z: Fill missing sample m/z with library m/z
        combined_df["m/z"] = combined_df["m/z_sample"].fillna(
            combined_df["m/z_library"]
        )

        # Consolidate CCS: Prioritize sample CCS, fill with library CCS
        # Gracefully handle if CCS columns don't exist
        ccs_sample = (
            combined_df["CCS_sample"]
            if "CCS_sample" in combined_df.columns
            else pd.Series(dtype="float")
        )
        ccs_library = (
            combined_df["CCS_library"]
            if "CCS_library" in combined_df.columns
            else pd.Series(dtype="float")
        )
        combined_df["CCS"] = ccs_sample.fillna(ccs_library)

        # Consolidate Name: Prioritize library Name, fill with sample Name
        # Gracefully handle if Name columns don't exist
        name_sample = (
            combined_df["Name_sample"]
            if "Name_sample" in combined_df.columns
            else pd.Series(dtype="object")
        )
        name_library = (
            combined_df["Name_library"]
            if "Name_library" in combined_df.columns
            else pd.Series(dtype="object")
        )
        combined_df["Name"] = name_library.fillna(name_sample)

        # 7. Create the final, clean DataFrame with only the desired columns
        final_columns = ["m/z", "CCS", "Origin", "Name"]

        # Ensure we only select columns that actually exist to prevent errors
        columns_to_keep = [col for col in final_columns if col in combined_df.columns]

        final_df = combined_df[columns_to_keep]

        print(
            f"\nSuccessfully created final simplified DataFrame with shape: {final_df.shape}"
        )

        return final_df

    except FileNotFoundError as e:
        print(f"ERROR: File not found. Please check the path: {e.filename}")
        return None
    except Exception as e:
        print(f"An error occurred during data processing: {e}")
        return None


def find_homologous_series(df, selected_repeating_units, mass_error_ppm=10):
    """
    Identifies homologous series trends by checking for repeating mass units
    based on m/z, CCS, Name, and Origin values.

    Args:
        df (pd.DataFrame): Input dataset with 'm/z', 'CCS', 'Name', and 'Origin' columns.
        selected_repeating_units (dict): Dictionary of repeating units to check (e.g., {'CF2': 49.99}).
        mass_error_ppm (int): PPM error tolerance for matching m/z differences.

    Returns:
        pd.DataFrame: A DataFrame containing the identified homologous series,
                      with columns ['GroupID', 'm/z', 'CCS', 'Name', 'Origin', 'Repeating Unit'].
    """
    # --- Input Validation ---
    required_cols = ["m/z", "CCS", "Name", "Origin"]
    if not isinstance(df, pd.DataFrame) or not all(
        col in df.columns for col in required_cols
    ):
        print(f"[ERROR] Input must be a DataFrame with {required_cols} columns.")
        return pd.DataFrame()

    if not isinstance(selected_repeating_units, dict) or not selected_repeating_units:
        print("[ERROR] 'selected_repeating_units' must be a non-empty dictionary.")
        return pd.DataFrame()

    # Ensure data is numeric and sorted by m/z for efficient searching
    df["m/z"] = pd.to_numeric(df["m/z"], errors="coerce")
    df["CCS"] = pd.to_numeric(df["CCS"], errors="coerce")
    df.dropna(subset=["m/z", "CCS"], inplace=True)

    if df.empty:
        print("[WARNING] DataFrame is empty after cleaning. No data to process.")
        return pd.DataFrame()

    df = df.sort_values(by="m/z").reset_index(drop=True)

    # --- Series Identification ---
    all_groups = []
    group_counter = 0

    for unit_name, M in selected_repeating_units.items():
        processed_indices = (
            set()
        )  # Tracks indices already assigned to a group for this unit

        for i in range(len(df)):
            if i in processed_indices:
                continue

            # Start a new potential group with the current point, now including Name and Origin
            current_group = [
                {
                    "m/z": df.at[i, "m/z"],
                    "CCS": df.at[i, "CCS"],
                    "Name": df.at[i, "Name"],
                    "Origin": df.at[i, "Origin"],
                }
            ]

            last_mz = df.at[i, "m/z"]

            # Search forward from the current point for the next member of the series
            for j in range(i + 1, len(df)):
                next_mz = df.at[j, "m/z"]
                mass_diff = next_mz - last_mz

                # Calculate the tolerance based on the current m/z
                tolerance = (mass_error_ppm / 1e6) * next_mz

                # Check if the mass difference matches the repeating unit within the tolerance
                if abs(mass_diff - M) <= tolerance:
                    current_group.append(
                        {
                            "m/z": df.at[j, "m/z"],
                            "CCS": df.at[j, "CCS"],
                            "Name": df.at[j, "Name"],
                            "Origin": df.at[j, "Origin"],
                        }
                    )
                    last_mz = (
                        next_mz  # Update the last_mz to search from this new point
                    )

            # A homologous series must have at least 3 points to be valid
            if len(current_group) >= 3:
                group_counter += 1
                group_df = pd.DataFrame(current_group)
                group_df["GroupID"] = group_counter
                group_df["Repeating Unit"] = unit_name
                all_groups.append(group_df)

                # Mark all indices from the valid group as processed
                for point in current_group:
                    original_index = df[df["m/z"] == point["m/z"]].index[0]
                    processed_indices.add(original_index)

    if not all_groups:
        print("[INFO] No homologous series with 3 or more points were found.")
        return pd.DataFrame()

    # Combine all found groups into a single DataFrame
    final_df = pd.concat(all_groups, ignore_index=True)

    # Reorder columns for clarity, now including 'Name' and 'Origin'
    final_df = final_df[["GroupID", "m/z", "CCS", "Name", "Origin", "Repeating Unit"]]

    print(
        f"[INFO] Analysis complete. Found {final_df['GroupID'].nunique()} homologous series."
    )
    return final_df


def main():
    """Run the analysis pipeline and return results."""
    # NOTE: Ensure these paths are correct for your system
    file_path = r"PIMMS v1.2\data\250918_SealsPIMMS (2).csv"
    library_file_path = r"PIMMS v1.2\import folder\level_2_library.csv"

    # The function now returns the clean, simplified DataFrame
    adjusted_df = load_and_combine_data(file_path, library_file_path)
    repeating_units = {"CF2": 49.9968064}

    homologous_series_df = find_homologous_series(
        adjusted_df,
        selected_repeating_units=repeating_units,
        mass_error_ppm=10,  # Using a large tolerance for this simple example
    )
    print(homologous_series_df)


if __name__ == "__main__":
    main()
