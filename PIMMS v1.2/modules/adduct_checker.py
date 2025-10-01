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


def find_matching_mass_relationships(df, mass_error_ppm=15):
    """Finds all relevant mass relationships within ppm bounds and removes matched m/z2 rows."""
    mz_values = sorted(df["m/z"].dropna().unique())

    # Offset constants
    offset_h = 1.007825
    offset_na = 21.981945
    offset_k = 37.9558834
    offset_ammonium = 17.0265478
    offset_li = 6.0081804

    matching_pairs = []
    matched_mz2_set = set()

    for mz1 in mz_values:
        if mz1 in matched_mz2_set:
            continue  # skip if this was already matched as an mz2

        # Compute theoretical target masses
        targets = [
            (mz1 + offset_na, "Δ ≈ Na"),
            (mz1 + offset_k, "Δ ≈ K"),
            (mz1 + offset_ammonium, "Δ ≈ NH4+"),
            (mz1 + offset_li, "Δ ≈ Li"),
            (2 * mz1 + offset_h, "2*m/z1 + H"),
            (2 * mz1 + offset_na, "2*m/z1 + Na"),
            (2 * mz1 + offset_k, "2*m/z1 + K"),
            (2 * mz1 + offset_ammonium, "2*m/z1 + NH4+"),
            (2 * mz1 + offset_li, "2*m/z1 + Li"),
        ]

        for target_mass, label in targets:
            hits = find_similar_peaks(mz_values, target_mass, mass_error_ppm)
            for mz2 in hits:
                matching_pairs.append((mz1, mz2, mz2 - mz1, label))
                matched_mz2_set.add(mz2)

    # Remove rows from original dataframe with matched m/z 2 values
    filtered_df = df[~df["m/z"].isin(matched_mz2_set)].reset_index(drop=True)

    return filtered_df
