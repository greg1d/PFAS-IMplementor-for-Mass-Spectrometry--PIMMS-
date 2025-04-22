from Kaufman_plotting import show_multi_peak_compound_matches
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd
import re
import numpy as np
from Kaufman_plotting import compute_kaufman_constants
from CF2_prioritization import (
    compute_mCm_alignment,
    compute_MDCm_alignment,
    cf2_prioritization,
)
from FC_prediction import FC_prediction


def label_isotopic_peaks(df):
    """
    Labels isotopic peaks (M, M+1, M+2...) for each (SampleName, Compound) group.

    Parameters:
        df (pd.DataFrame): Must contain columns ['SampleName', 'Compound', 'Peak_mz']

    Returns:
        pd.DataFrame: Original dataframe with new column 'Isotope_Label'
    """
    if not {"SampleName", "Compound", "Peak_mz"}.issubset(df.columns):
        raise ValueError(
            "Input DataFrame must contain 'SampleName', 'Compound', and 'Peak_mz' columns."
        )

    df = df.copy()
    df["Isotope_Label"] = None

    grouped = df.groupby(["SampleName", "Compound"])

    for (sample, compound), group in grouped:
        sorted_group = group.sort_values("Peak_mz").reset_index()
        for i, idx in enumerate(sorted_group["index"]):
            df.at[idx, "Isotope_Label"] = f"M+{i}" if i > 0 else "M"

    return df


def normalize_isotopic_intensity(df):
    """
    Normalizes Peak_intensity in each (SampleName, Compound) group by the intensity of the M peak (maximum).

    Parameters:
        df (pd.DataFrame): Must contain 'SampleName', 'Compound', and 'Peak_intensity'

    Returns:
        pd.DataFrame: Original dataframe with an additional 'Normalized_Intensity' column
    """
    if not {"SampleName", "Compound", "Peak_intensity"}.issubset(df.columns):
        raise ValueError(
            "Input DataFrame must contain 'SampleName', 'Compound', and 'Peak_intensity' columns."
        )

    df = df.copy()
    df["Normalized_Intensity"] = df.groupby(["SampleName", "Compound"])[
        "Peak_intensity"
    ].transform(lambda x: x / x.max() if x.max() != 0 else 0)

    return df


"""
# Citations

- [DOI: 10.1351/PAC-REP-10-06-02](https://doi.org/10.1351/PAC-REP-10-06-02)
- J. S. Coursey, D. J. Schwab, J. J. Tsai, and R. A. Dragoset
- NIST Physical Measurement Laboratory
- [IOP Science Article](https://iopscience.iop.org/article/10.1088/1674-1137/36/12/003)
- [CIAAW Atomic Weights](https://www.ciaaw.org/atomic-weights.htm)
"""


def read_isotope_data(file_path):
    """Read the isotope data from the given file path."""
    with open(file_path, "r") as file:
        data = file.read()
    return data


def parse_isotope_data(data):
    """Parse the isotope data from the given string."""
    # Define regex patterns for each field
    patterns = {
        "Atomic Number": re.compile(r"Atomic Number = (\d+)"),
        "Atomic Symbol": re.compile(r"Atomic Symbol = (\w+)"),
        "Mass Number": re.compile(r"Mass Number = (\d+)"),
        "Relative Atomic Mass": re.compile(r"Relative Atomic Mass = ([\d.]+)"),
        "Isotopic Composition": re.compile(r"Isotopic Composition = ([\d.]+)"),
        "Standard Atomic Weight": re.compile(r"Standard Atomic Weight = ([\d.,\[\]]+)"),
        "Notes": re.compile(r"Notes = (\w*)"),
    }

    # Initialize lists to store the parsed data
    data_dict = {key: [] for key in patterns.keys()}

    # Split the data into lines
    lines = data.split("\n")

    # Process the lines in chunks corresponding to each data point
    chunk_size = 8  # Each data point is composed of 7 lines followed by a blank line
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]
        for key, pattern in patterns.items():
            for line in chunk:
                if line.strip() == "":
                    continue  # Skip blank lines
                match = pattern.search(line)
                if match:
                    value = match.group(1)
                    if key in ["Relative Atomic Mass", "Isotopic Composition"]:
                        value = re.sub(
                            r"\(.*\)", "", value
                        ).strip()  # Remove values in parentheses
                    if key == "Isotopic Composition" and value == "":
                        value = None  # Treat empty isotopic composition as None
                    data_dict[key].append(value)
                    break
            else:
                data_dict[key].append(None)  # Append None if no match is found

    # Create a DataFrame from the parsed data
    df = pd.DataFrame(data_dict)

    # Exclude rows with empty Isotopic Composition
    df = df[df["Isotopic Composition"].notna()]

    # Drop the Notes column
    df = df.drop(columns=["Notes"])

    return df


def add_elemental_symbol(df, csv_path):
    """Add the Elemental Symbol column to the DataFrame based on the Atomic Number."""
    # Read the CSV file
    atomic_numbers_df = pd.read_csv(csv_path)

    # Ensure both columns have the same data type
    df = df.dropna(subset=["Atomic Number"])  # Drop rows where Atomic Number is None
    df["Atomic Number"] = df["Atomic Number"].astype(int)
    atomic_numbers_df["AtomicNumber"] = atomic_numbers_df["AtomicNumber"].astype(int)

    # Merge the DataFrame with the atomic numbers DataFrame
    df = df.merge(
        atomic_numbers_df, left_on="Atomic Number", right_on="AtomicNumber", how="left"
    )

    # Rename the Symbol column to Elemental Symbol
    df = df.rename(columns={"Symbol": "Elemental Symbol"})

    # Drop the AtomicNumber column
    df = df.drop(columns=["AtomicNumber"])

    # Reorder columns to place Elemental Symbol as the second column
    cols = df.columns.tolist()
    cols.insert(1, cols.pop(cols.index("Elemental Symbol")))
    df = df[cols]

    return df


def heavy_halogen_reader(isotope_df):
    """
    Identify Br, Cl, C, or F isotopic signatures based on normalized isotopic compositions.

    Parameters:
        isotope_df (pd.DataFrame): Contains reference isotopic distributions with:
                                   'Elemental Symbol', 'Relative Atomic Mass', 'Isotopic Composition'

    Returns:
        halogen_df (pd.DataFrame): Subset with Br/Cl/C/F isotopes, labeled and normalized
    """

    # Filter for Br, Cl, C, F
    halogen_df = isotope_df[
        isotope_df["Elemental Symbol"].isin(["Br", "Cl", "C", "F"])
    ].copy()

    # Ensure correct types
    halogen_df["Relative Atomic Mass"] = halogen_df["Relative Atomic Mass"].astype(
        float
    )
    halogen_df["Isotopic Composition"] = halogen_df["Isotopic Composition"].astype(
        float
    )

    # Sort for consistent labeling
    halogen_df.sort_values(
        by=["Elemental Symbol", "Relative Atomic Mass"], inplace=True
    )

    # Compute Isotope_Label dynamically
    halogen_df["Isotope_Label"] = None
    for element in halogen_df["Elemental Symbol"].unique():
        group = halogen_df[halogen_df["Elemental Symbol"] == element].copy()
        base_mass = group["Relative Atomic Mass"].min()
        for idx, row in group.iterrows():
            diff = row["Relative Atomic Mass"] - base_mass
            label = f"M+{int(round(diff))}"  # Round mass difference to nearest integer
            halogen_df.at[idx, "Isotope_Label"] = label

    # Normalize intensities per element group
    halogen_df["Normalized_Intensity"] = halogen_df.groupby("Elemental Symbol")[
        "Isotopic Composition"
    ].transform(lambda x: x / x.max())

    return halogen_df


def compute_isotopic_distribution(element_df, element_symbol="Cl", count=2):
    """
    Computes the normalized isotopic distribution for a given element and atom count using convolution.
    """
    filtered = element_df[element_df["Elemental Symbol"] == element_symbol].copy()

    if filtered.empty:
        raise ValueError(f"No isotopic data found for element: {element_symbol}")

    # Fix: convert Isotope_Label to Isotope_Order as integer
    filtered["Isotope_Order"] = (
        filtered["Isotope_Label"].str.replace("M", "0").str.replace("+", "").astype(int)
    )

    filtered = filtered.sort_values("Isotope_Order")
    intensities = filtered["Normalized_Intensity"].values

    distribution = intensities.copy()
    for _ in range(count - 1):
        distribution = np.convolve(distribution, intensities)

    distribution /= distribution.max()
    labels = [f"M+{i * 2}" for i in range(len(distribution))]

    return pd.DataFrame(
        {
            "Isotope_Label": labels,
            "Normalized_Intensity": distribution,
            "Combination": f"{element_symbol}{count}",
        }
    )


def compute_mixed_isotopic_distribution(halogen_df, max_atoms=3):
    """
    Computes isotopic distributions for all combinations of 1–3 Cl and 1–3 Br atoms,
    inserting zeroes at odd-numbered M+1, M+3, etc., to keep uniform labeling.
    """
    results = []

    for cl_count in range(0, max_atoms + 1):
        for br_count in range(0, max_atoms + 1):
            if cl_count == 0 and br_count == 0:
                continue

            cl_dist = (
                compute_isotopic_distribution(halogen_df, "Cl", cl_count)
                if cl_count > 0
                else pd.DataFrame({"Normalized_Intensity": [1.0]})
            )
            br_dist = (
                compute_isotopic_distribution(halogen_df, "Br", br_count)
                if br_count > 0
                else pd.DataFrame({"Normalized_Intensity": [1.0]})
            )

            # Perform convolution
            combined = np.convolve(
                cl_dist["Normalized_Intensity"], br_dist["Normalized_Intensity"]
            )
            combined /= combined.max()  # Normalize to max = 1

            # Insert 0s into odd M+ positions (i.e., M+1, M+3, etc.)
            extended = []
            for i in range(len(combined) * 2 - 1):
                if i % 2 == 0:
                    extended.append(combined[i // 2])
                else:
                    extended.append(0.0)

            labels = [f"M+{i}" for i in range(len(extended))]
            combination = f"Cl{cl_count}_Br{br_count}"

            df = pd.DataFrame(
                {
                    "Isotope_Label": labels,
                    "Normalized_Intensity": extended,
                    "Combination": combination,
                }
            )

            results.append(df)

    return pd.concat(results, ignore_index=True)


def merging_kaufman_df_with_isotopic_modeling(kaufman_df, multi_peak_df):
    """
    Adds the Predicted_F_per_C value from kaufman_df into multi_peak_df
    by matching on SampleName and Compound. Leaves all other columns in
    multi_peak_df unchanged.

    Parameters:
        kaufman_df (pd.DataFrame): Must contain ['Sample', 'Compound', 'Predicted_F_per_C']
        multi_peak_df (pd.DataFrame): Must contain ['SampleName', 'Compound']

    Returns:
        pd.DataFrame: Updated multi_peak_df with added Predicted_F_per_C column
    """
    # Create a lookup table from kaufman_df
    lookup = kaufman_df.set_index(["Sample", "Compound"])["Predicted_F_per_C"]

    # Map the predicted F/C value into multi_peak_df using SampleName as the key
    multi_peak_df = multi_peak_df.copy()
    multi_peak_df["Predicted_F_per_C"] = multi_peak_df.apply(
        lambda row: lookup.get((row["SampleName"], row["Compound"]), pd.NA), axis=1
    )

    return multi_peak_df


def compute_max_possible_f_to_c(multi_peak_df):
    """
    Compute the maximum number of Carbon and Fluorine atoms possible given Peak_mz_1 and Predicted_F_per_C.

    Parameters:
        matches_df (pd.DataFrame): Must contain 'Peak_mz_1' and 'Predicted_F_per_C'

    Returns:
        pd.DataFrame: Original dataframe with 'Max_Carbons' and 'Max_Fluorines' columns added
    """
    if (
        "Peak_mz_1" not in multi_peak_df.columns
        or "Predicted_F_per_C" not in multi_peak_df.columns
    ):
        raise ValueError(
            "Input DataFrame must contain 'Peak_mz_1' and 'Predicted_F_per_C' columns."
        )

    atomic_mass_C = 12.00000
    atomic_mass_F = 18.9984032

    def calculate_limits(row):
        max_carbons = int(
            row["Peak_mz_1"]
            / (atomic_mass_C + row["Predicted_F_per_C"] * atomic_mass_F)
        )
        max_fluorines = int(row["Predicted_F_per_C"] * max_carbons)
        return pd.Series({"Max_Carbons": max_carbons, "Max_Fluorines": max_fluorines})

    result = multi_peak_df.copy()
    result[["Max_Carbons", "Max_Fluorines"]] = result.apply(calculate_limits, axis=1)
    return result


def heavy_halogen_isotopic_matching(labeled_df, theoretical_df):
    """
    Match experimental isotopic patterns to theoretical ones based on Isotope_Label and Normalized_Intensity.
    For each (SampleName, Compound) group, only the best match (lowest Avg_Diff) is retained.
    """
    if labeled_df is None or theoretical_df is None:
        raise ValueError("Input DataFrames cannot be None.")

    labeled_df = labeled_df.copy()
    labeled_df["Isotope_Label"] = (
        labeled_df["Isotope_Label"].str.strip().replace("M", "M+0")
    )

    theoretical_df = theoretical_df.copy()

    # Normalize Isotope_Label using atomic mass differences
    if (
        "Relative Atomic Mass" in theoretical_df.columns
        and "Elemental Symbol" in theoretical_df.columns
    ):
        theoretical_df["Isotope_Label"] = None
        for element in theoretical_df["Elemental Symbol"].unique():
            group = theoretical_df[theoretical_df["Elemental Symbol"] == element]
            base_mass = group["Relative Atomic Mass"].min()
            for idx, row in group.iterrows():
                diff = row["Relative Atomic Mass"] - base_mass
                theoretical_df.at[idx, "Isotope_Label"] = f"M+{int(round(diff))}"
    else:
        theoretical_df["Isotope_Label"] = (
            theoretical_df["Isotope_Label"].str.strip().replace("M", "M+0")
        )

    all_matches = []

    grouped = labeled_df.groupby(["SampleName", "Compound"])

    for (sample, compound), group_df in grouped:
        best_combination = None
        best_avg_diff = float("inf")
        best_merged = pd.DataFrame()

        for combination, ref_group in theoretical_df.groupby("Combination"):
            merged = pd.merge(
                group_df,
                ref_group,
                how="inner",
                on="Isotope_Label",
                suffixes=("_exp", "_ref"),
            )

            if merged.empty:
                continue

            merged["Isotope_Order"] = (
                merged["Isotope_Label"]
                .str.extract(r"M\+(\d+)", expand=False)
                .fillna("0")
                .astype(int)
            )
            merged["Intensity_Diff"] = (
                merged["Normalized_Intensity_exp"] - merged["Normalized_Intensity_ref"]
            ).abs()

            avg_diff = merged["Intensity_Diff"].mean()

            if avg_diff < best_avg_diff:
                best_avg_diff = avg_diff
                best_combination = combination
                best_merged = merged.copy()

        # Only keep the best one
        if not best_merged.empty:
            for _, row in best_merged.iterrows():
                all_matches.append(
                    {
                        "SampleName": row["SampleName"],
                        "Compound": row["Compound"],
                        "Combination": best_combination,
                        "Isotope_Label": row["Isotope_Label"],
                        "Normalized_Intensity_exp": row["Normalized_Intensity_exp"],
                        "Normalized_Intensity_ref": row["Normalized_Intensity_ref"],
                        "Intensity_Diff": row["Intensity_Diff"],
                        "Avg_Diff": best_avg_diff,
                    }
                )

    return pd.DataFrame(all_matches) if all_matches else pd.DataFrame()


def add_predicted_f_to_matches(matches_df, kaufman_df):
    """
    Merge Predicted_F_per_C from kaufman_df into matches_df based on SampleName and Compound.

    Parameters:
        matches_df (pd.DataFrame): Output from heavy_halogen_isotopic_matching
        kaufman_df (pd.DataFrame): Contains Predicted_F_per_C, Sample, Compound

    Returns:
        pd.DataFrame: matches_df with added Predicted_F_per_C column
    """
    if matches_df.empty:
        print("[INFO] matches_df is empty, skipping merge.")
        return matches_df

    # Rename 'Sample' in kaufman_df to 'SampleName' to align with matches_df
    kaufman_df_renamed = kaufman_df.rename(columns={"Sample": "SampleName"})
    merged_df = pd.merge(
        matches_df,
        kaufman_df_renamed[
            ["SampleName", "Compound", "Predicted_F_per_C", "Peak_mz_1"]
        ],
        on=["SampleName", "Compound"],
        how="left",
    )

    return merged_df


def compute_cf_isotopic_distributions(matches_df, halogen_df):
    """
    Computes isotopic distributions up to M+6 for each row in matches_df using Max_Carbons and Max_Fluorines.
    Keeps natural isotopic contributions without forcing zeros at odd M positions.

    Parameters:
        matches_df (pd.DataFrame): Must contain 'Max_Carbons' and 'Max_Fluorines'
        halogen_df (pd.DataFrame): Output from heavy_halogen_reader including C and F

    Returns:
        pd.DataFrame: Combined isotopic distribution (up to M+6) with SampleName and Compound context
    """
    all_results = []

    for idx, row in matches_df.iterrows():
        sample = row["SampleName"]
        compound = row["Compound"]
        max_c = int(row.get("Max_Carbons", 0))
        max_f = int(row.get("Max_Fluorines", 0))

        carbon_dist = (
            compute_isotopic_distribution(halogen_df, "C", max_c)
            if max_c > 0
            else pd.DataFrame({"Normalized_Intensity": [1.0]})
        )
        fluorine_dist = (
            compute_isotopic_distribution(halogen_df, "F", max_f)
            if max_f > 0
            else pd.DataFrame({"Normalized_Intensity": [1.0]})
        )

        combined = np.convolve(
            carbon_dist["Normalized_Intensity"], fluorine_dist["Normalized_Intensity"]
        )
        combined /= combined.max()

        # Only take M through M+6
        labels = [f"M+{i}" for i in range(min(len(combined), 7))]
        intensities = combined[:7]

        result_df = pd.DataFrame(
            {
                "SampleName": sample,
                "Compound": compound,
                "Isotope_Label": labels,
                "Normalized_Intensity": intensities,
                "Combination": f"C{max_c}_F{max_f}",
            }
        )
        all_results.append(result_df)

    return pd.concat(all_results, ignore_index=True)


def cf_isotopic_matching_filtered(labeled_df, cf_theoretical_df, matches_df):
    """
    Match experimental isotopic patterns to CF-only theoretical patterns using Isotope_Label and Normalized_Intensity.
    Uses the Max_Carbons and Max_Fluorines values per SampleName + Compound pair to filter correct theoretical match.
    Reports Avg_Diff for every valid match regardless of error.
    """
    if labeled_df is None or cf_theoretical_df is None or matches_df is None:
        raise ValueError("Input DataFrames cannot be None.")

    labeled_df = labeled_df.copy()
    cf_theoretical_df = cf_theoretical_df.copy()
    matches_df = matches_df.copy()

    labeled_df["Isotope_Label"] = (
        labeled_df["Isotope_Label"].str.strip().replace("M", "M+0")
    )
    cf_theoretical_df["Isotope_Label"] = (
        cf_theoretical_df["Isotope_Label"].str.strip().replace("M", "M+0")
    )

    matches = []
    grouped_exp = labeled_df.groupby(["SampleName", "Compound"])

    for (sample, compound), group_df in grouped_exp:
        match_row = matches_df[
            (matches_df["SampleName"] == sample) & (matches_df["Compound"] == compound)
        ]

        if match_row.empty:
            continue

        max_c = int(match_row["Max_Carbons"].values[0])
        max_f = int(match_row["Max_Fluorines"].values[0])
        expected_label = f"C{max_c}_F{max_f}"

        theoretical_subset = cf_theoretical_df[
            (cf_theoretical_df["SampleName"] == sample)
            & (cf_theoretical_df["Compound"] == compound)
            & (cf_theoretical_df["Combination"] == expected_label)
        ]

        if theoretical_subset.empty:
            print(
                f"[DEBUG] No theoretical match for {sample}, {compound}, {expected_label}"
            )
            continue

        merged = pd.merge(
            group_df, theoretical_subset, on="Isotope_Label", suffixes=("_exp", "_cf")
        )

        if merged.empty:
            print(f"[DEBUG] No merge result for {sample}, {compound}")
            continue

        merged["Isotope_Order"] = (
            merged["Isotope_Label"]
            .str.extract(r"M\+(\d+)", expand=False)
            .fillna("0")
            .astype(int)
        )
        merged["Intensity_Diff"] = (
            merged["Normalized_Intensity_exp"] - merged["Normalized_Intensity_cf"]
        ).abs()

        avg_diff = merged["Intensity_Diff"].mean()

        for _, row in merged.iterrows():
            matches.append(
                {
                    "SampleName": sample,
                    "Compound": compound,
                    "Isotope_Label": row["Isotope_Label"],
                    "Normalized_Intensity_exp": row["Normalized_Intensity_exp"],
                    "Normalized_Intensity_cf": row["Normalized_Intensity_cf"],
                    "Intensity_Diff": row["Intensity_Diff"],
                    "Avg_Diff": avg_diff,
                    "Combination": expected_label,
                }
            )

    if not matches:
        print("[INFO] No matches found.")
        return pd.DataFrame()

    return pd.DataFrame(matches).drop_duplicates()


def merge_matches_and_cf_results(matches, cf_results):
    """
    Merges halogen (matches) and CF-only (cf_results) isotopic match results
    by SampleName and Compound. Adds CF_Avg_Diff and CF_Combination columns to matches.

    Parameters:
        matches (pd.DataFrame): Halogen-based matching results
        cf_results (pd.DataFrame): CF-only matching results

    Returns:
        pd.DataFrame: Merged DataFrame with CF info included in matches.
    """
    # Reduce CF results to one row per SampleName + Compound (assuming one match per group)
    cf_summary = cf_results[
        ["SampleName", "Compound", "Avg_Diff", "Combination"]
    ].drop_duplicates()
    cf_summary = cf_summary.rename(
        columns={"Avg_Diff": "CF_Avg_Diff", "Combination": "CF_Combination"}
    )

    # Merge on both SampleName and Compound
    merged = matches.merge(cf_summary, on=["SampleName", "Compound"], how="left")

    return merged


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    file_path = r"PIMMS v1.2\CEF_reading\data\Isotopic modelling values (NIST).txt"
    csv_path = r"PIMMS v1.2\CEF_reading\data\Atomic numbers for elements.csv"

    # === Load and match CEF files ===
    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        return pd.DataFrame()

    # === Compute Kaufman Constants and Prioritization ===
    kaufman_df = compute_kaufman_constants(multi_peak_df)
    kaufman_df = compute_mCm_alignment(kaufman_df)
    kaufman_df = compute_MDCm_alignment(kaufman_df)
    kaufman_df = cf2_prioritization(kaufman_df)
    kaufman_df = FC_prediction(kaufman_df)

    # === Load and process elemental isotope reference data ===
    data = read_isotope_data(file_path)
    isotope_data = parse_isotope_data(data)
    isotope_data = add_elemental_symbol(isotope_data, csv_path)

    # === Reload multi-peak data and merge Kaufman predictions ===
    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    multi_peak_df = show_multi_peak_compound_matches(matches, cef_folder)
    if multi_peak_df.empty:
        return pd.DataFrame()

    multi_peak_df = merging_kaufman_df_with_isotopic_modeling(kaufman_df, multi_peak_df)

    # === Isotopic labeling and normalization ===
    labeled_df = label_isotopic_peaks(multi_peak_df)
    labeled_df = normalize_isotopic_intensity(labeled_df)

    # === Generate halogen isotope reference models ===
    halogen_isotopes = heavy_halogen_reader(isotope_data)
    theoretical_df = compute_mixed_isotopic_distribution(halogen_isotopes)
    # === Run halogen-based isotopic matching ===
    matches = heavy_halogen_isotopic_matching(labeled_df, theoretical_df)
    # === Predict C/F ratios and estimate max elemental counts ===
    matches = add_predicted_f_to_matches(matches, kaufman_df)
    matches = compute_max_possible_f_to_c(matches)

    # === Generate C/F theoretical distributions ===
    cf_theoretical_df = compute_cf_isotopic_distributions(matches, halogen_isotopes)
    # === Match experimental patterns to CF-only theoretical ones ===
    cf_results = cf_isotopic_matching_filtered(
        labeled_df=labeled_df,
        cf_theoretical_df=cf_theoretical_df,
        matches_df=matches,
    )
    # === Merge halogen and CF results ===
    all_matches = merge_matches_and_cf_results(matches, cf_results)
    all_matches.to_csv(r"PIMMS v1.2\Data_output\heavy_halogen_matches.csv", index=False)


if __name__ == "__main__":
    main()
