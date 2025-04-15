import pandas as pd
import bisect

mass_error_ppm = 15


def calculate_mass_error_no_charge(mass, mass_error_ppm):
    """Calculate the absolute mass error based on ppm."""
    return mass * mass_error_ppm * 1e-6


def find_similar_peaks(array, target_mass, mass_error_ppm):
    """Finds peaks within the mass error bounds using binary search based on the higher target mass."""
    mass_bound = calculate_mass_error_no_charge(target_mass, mass_error_ppm)
    lower_bound = target_mass - mass_bound
    upper_bound = target_mass + mass_bound

    print(
        f"Searching for: {target_mass:.6f} ± {mass_bound:.6f} ppm → bounds: [{lower_bound:.6f}, {upper_bound:.6f}]"
    )

    j_start = bisect.bisect_left(array, lower_bound)
    j_end = bisect.bisect_right(array, upper_bound)
    return array[j_start:j_end]


def find_neutral_loss_matches(df, mass_error_ppm=15):
    """Finds neutral loss matches and removes m/z2 if Classification Type != 'Likely'."""
    mz_values = sorted(df["m/z"].dropna().unique())

    neutral_losses = [
        (43.9898, "M−CO2"),
        (27.9949, "M−CO"),
        (79.9568, "M−SO3"),
        (30.0106, "M−H2CO"),
        (97.9769, "M−H3PO4"),
        (98.9552, "M−FSO3"),
    ]

    matching_pairs = []
    mz2s_to_remove = set()

    for mz1 in mz_values:
        for offset, label in neutral_losses:
            target_mass = mz1 - offset
            if target_mass <= 0:
                continue

            hits = find_similar_peaks(mz_values, target_mass, mass_error_ppm)

            for mz2 in hits:
                matching_pairs.append((mz1, mz2, mz1 - mz2, label))

                # Check if m/z2's Classification Type is not "Likely"
                row = df[df["m/z"] == mz2]
                if not row.empty and row["Classification Type"].values[0] != "likely":
                    mz2s_to_remove.add(mz2)

    # Filter out only those m/z2s that are not 'Likely'
    filtered_df = df[~df["m/z"].isin(mz2s_to_remove)].reset_index(drop=True)

    return filtered_df


def main():
    file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set test.csv"
    df = pd.read_csv(file_path)
    filtered_df = find_neutral_loss_matches(df, mass_error_ppm)
    print(filtered_df)


if __name__ == "__main__":
    main()
