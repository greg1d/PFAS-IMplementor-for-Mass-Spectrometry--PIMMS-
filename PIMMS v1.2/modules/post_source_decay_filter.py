import pandas as pd
import bisect


def calculate_mass_error_no_charge(mass, mass_error_ppm=10):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, mass, mass_error_ppm=10):
    """Finds peaks within the mass error bounds using binary search."""
    mass_bound = calculate_mass_error_no_charge(mass, mass_error_ppm)
    lower_bound = mass - mass_bound
    upper_bound = mass + mass_bound

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)

    return array[j_start:j_end]


def remove_post_source_decay(adjusted_df):
    """Removes post-source decay candidates by keeping the feature with the lower CCS using ID-based removal."""

    print("\n[DEBUG] Starting Post-Source Decay Removal Process")

    # Extract 'likely' features
    likely_df = adjusted_df[adjusted_df["Classification Type"] == "likely"].copy()
    print(f"[DEBUG] Found {len(likely_df)} likely features to check.")

    # Extract other features (potential decay products)
    other_df = adjusted_df[adjusted_df["Classification Type"] != "likely"].copy()
    print(f"[DEBUG] Found {len(other_df)} potential decay candidates.")

    # Sort other_df by mass for binary search
    other_df = other_df.sort_values(by="m/z").reset_index(
        drop=True
    )  # Keep original IDs intact

    # Convert mass column to a sorted list for binary search
    mass_array = other_df["m/z"].tolist()

    decay_ids = set()  # Store decay candidate IDs

    for _, likely_row in likely_df.iterrows():
        likely_mass = likely_row["m/z"]
        likely_rt = likely_row["RT"]
        likely_ccs = likely_row["CCS"]
        likely_id = likely_row["ID"]  # Get ID of likely feature

        print(
            f"\n[DEBUG] Checking likely feature: ID={likely_id}, m/z={likely_mass}, RT={likely_rt}, CCS={likely_ccs}"
        )

        # Find mass matches within 10 ppm
        matching_masses = find_similar_peaks(mass_array, likely_mass, mass_error_ppm=10)
        print(
            f"[DEBUG] Found {len(matching_masses)} mass matches within 10 ppm: {matching_masses}"
        )

        # Iterate through possible matches
        for match_mass in matching_masses:
            match_row = other_df[other_df["m/z"] == match_mass]

            if match_row.empty:
                continue  # Skip if no match found

            match_rt = match_row["RT"].values[0]
            match_ccs = match_row["CCS"].values[0]
            match_id = match_row["ID"].values[0]  # ✅ Store ID instead of index

            print(
                f"  [DEBUG] Potential decay match: ID={match_id}, m/z={match_mass}, RT={match_rt}, CCS={match_ccs}"
            )

            # Apply filtering criteria
            if abs(likely_rt - match_rt) < 0.1 and match_ccs >= likely_ccs * 1.03:
                print("  [DEBUG] ✅ Matched as decay candidate!")

                # Ensure we remove the feature with the **higher** CCS
                if match_ccs > likely_ccs:
                    print(
                        f"  [DEBUG] Removing ID {match_id} (Decay Feature with higher CCS)"
                    )
                    decay_ids.add(match_id)
                else:
                    print(
                        "  [DEBUG] Skipping removal since likely feature has higher CCS."
                    )

    # Print IDs that will be removed
    print(
        f"\n[DEBUG] Removing {len(decay_ids)} post-source decay candidates: {decay_ids}"
    )

    # Remove post-source decay candidates using ID
    adjusted_df = adjusted_df[~adjusted_df["ID"].isin(decay_ids)].reset_index(drop=True)

    print("[DEBUG] Finished Post-Source Decay Removal Process.\n")

    return adjusted_df


def main():
    """Main function to test the PSD filter with a sample dataset."""

    # Example adjusted_df with rows to process
    adjusted_df = pd.DataFrame(
        {
            "ID": [1, 2, 3, 4, 5],
            "RT": [3, 3.4, 3.665, 3.066, 3.664],
            "DT": [23.175, 22.024, 23.130, 23.407, 24.319],
            "CCS": [175.79, 176.79, 175.79, 185.79, 175.79],
            "m/z": [100, 100.00012, 200, 100, 400],
            "Classification Type": [
                "likely",
                "tentative",
                "likely",
                "unmatched",
                "tentative",
            ],
            "148 B2 16632.d.DeMP": [0, 10, 10, 10, 10],
            "149 B2 16631.d.DeMP": [1, 20, 10, 10, 10],
        }
    )

    print("\n[INFO] Original adjusted_df:")
    print(adjusted_df)

    # Run Post-Source Decay Removal
    filtered_df = remove_post_source_decay(adjusted_df)

    print("\n[INFO] Updated adjusted_df after removing post-source decay:")
    print(filtered_df)


if __name__ == "__main__":
    main()
