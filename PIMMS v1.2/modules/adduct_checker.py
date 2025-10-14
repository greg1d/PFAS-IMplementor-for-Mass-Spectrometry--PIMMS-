import bisect

mass_error_ppm = 15


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, target_mass, mass_error_ppm):
    """Finds peaks within the mass error bounds using binary search based on the target mass (higher)."""
    mass_bound = calculate_mass_error_no_charge(target_mass, mass_error_ppm)
    lower_bound = target_mass - mass_bound
    upper_bound = target_mass + mass_bound

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    return array[j_start:j_end]


def adduct_removal(df):
    """Finds all relevant mass relationships within ppm bounds and removes matched m/z2 rows
    only if Classification Type is 'unmatched' or 'tentative'."""

    mz_values = sorted(df["m/z"].dropna().unique())
    mass_error_ppm = 10

    # Offset constants
    offset_h = 1.007825
    offset_na = 21.981945
    offset_ammonium = 17.0265478

    matching_pairs = []
    matched_mz2_set = set()

    for mz1 in mz_values:
        if mz1 in matched_mz2_set:
            continue  # skip if this was already matched as an mz2

        # Compute theoretical target masses
        targets = [
            (2 * mz1 + offset_h, "2*m/z1 + H"),
            (3 * mz1 + 2 * offset_h, "3*m/z1 + 2H"),
            (mz1 + offset_na - offset_h, "m/z1 + Na - H"),
            (mz1 + offset_ammonium - offset_h, "m/z1 + NH4 - H"),
            (2 * mz1 + offset_na, "2*m/z1 + Na"),
            (3 * mz1 + 2 * offset_ammonium, "3*m/z1 + 2NH4"),
            (3 * mz1 + 2 * offset_na, "3*m/z1 + 2Na"),
            (2 * mz1 + offset_ammonium, "2*m/z1 + NH4"),
            (3 * mz1 + offset_na + offset_ammonium, "3*m/z1 + Na + NH4"),
            (3 * mz1 + offset_h + offset_ammonium, "3*m/z1 + H + NH4"),
            (3 * mz1 + offset_h + offset_na, "3*m/z1 + H + Na"),
        ]

        for target_mass, label in targets:
            hits = find_similar_peaks(mz_values, target_mass, mass_error_ppm)
            for mz2 in hits:
                matching_pairs.append((mz1, mz2, mz2 - mz1, label))
                matched_mz2_set.add(mz2)

    # --- Remove rows only if Classification Type is 'unmatched' or 'tentative' ---
    to_remove_mask = df["m/z"].isin(matched_mz2_set) & df["Classification Type"].isin(
        ["unmatched", "tentative"]
    )
    filtered_df = df[~to_remove_mask].reset_index(drop=True)

    return filtered_df
