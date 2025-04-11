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

    # Extract 'likely' features
    likely_df = adjusted_df[adjusted_df["Classification Type"] == "likely"].copy()

    # Extract other features (potential decay products)
    other_df = adjusted_df[adjusted_df["Classification Type"] != "likely"].copy()

    # Sort other_df by mass for binary search
    other_df = other_df.sort_values(by="m/z").reset_index(
        drop=True
    )  # Keep original IDs intact

    # Convert mass column to a sorted list for binary search
    mass_array = other_df["m/z"].tolist()

    decay_ids = set()  # Store all decay candidate IDs

    for _, likely_row in likely_df.iterrows():
        likely_mass = likely_row["m/z"]
        likely_rt = likely_row["RT"]
        likely_ccs = likely_row["CCS"]

        # Find mass matches within 10 ppm
        matching_masses = find_similar_peaks(mass_array, likely_mass, mass_error_ppm=10)

        # Iterate through all possible matches
        for match_mass in matching_masses:
            matched_rows = other_df[other_df["m/z"] == match_mass]  # Get all matches

            if matched_rows.empty:
                continue  # Skip if no match found

            for _, match_row in matched_rows.iterrows():
                match_rt = match_row["RT"]
                match_ccs = match_row["CCS"]
                match_id = match_row["ID"]  # ✅ Store ID instead of index

                # Apply filtering criteria
                if abs(likely_rt - match_rt) < 1 and match_ccs >= likely_ccs * 1.03:
                    # Ensure we remove the feature with the **higher** CCS
                    if match_ccs > likely_ccs:
                        decay_ids.add(match_id)

    # Remove post-source decay candidates using ID
    adjusted_df = adjusted_df[~adjusted_df["ID"].isin(decay_ids)].reset_index(drop=True)

    return adjusted_df
