import glob
import os
import time

import pandas as pd

# Define the directory containing the CSV files - specify where all your fluoromatch files are
directory_path = r"F:\Twins Project (2.24-)\Non-target work\Processed Data\Test folder"

# Use glob to find all CSV files in the directory with "_FIN" in their name - All the fluoromatch files will end in _FIN if you use the code edit I used
csv_files = glob.glob(os.path.join(directory_path, "*_FIN*.csv"))

# Load the EPA library Excel file - I use the Kauffmann Master List as it has all the ionization forms as opposed to the EPA masterlist that spits things that don't make sense (-COOH where there are no oxygens e.g.)
epa_library_path = (
    r"F:\Twins Project (2.24-)\Non-target work\Import Folder\Kauffman M_H Library.xlsx"
)

if not os.path.exists(epa_library_path):
    print(f"File not found: {epa_library_path}")
else:
    print(f"File found: {epa_library_path}")

epa_library = pd.read_excel(epa_library_path)
library_masses = epa_library["MONOISOTOPIC MASS"].values
library_preferred_names = epa_library.set_index("MONOISOTOPIC MASS")[
    "PREFERRED NAME"
].to_dict()

# Load the neutral loss masses from the specified Excel file
neutral_loss_path = (
    r"F:\Twins Project (2.24-)\Non-target work\Import Folder\Neutral loss masses.xlsx"
)
neutral_loss_df = pd.read_excel(neutral_loss_path)
neutral_loss_masses = neutral_loss_df["Mass"].tolist()

# Here's where you're putting your library for standards - only CCS and m/z are needed
reference_excel_path = r"F:\Twins Project (2.24-)\Non-target work\Import Folder\MPFAC HIF ES SIL peaks.xlsx"
reference_peaks_df = pd.read_excel(
    reference_excel_path, sheet_name="MPFAC-HIF-ES Peaks"
)
# Wellington has the habit of occasionally making the stated label - 1, so I created an added sheet which is the listed mass -(C13-C12)
error_peaks_df = pd.read_excel(
    reference_excel_path, sheet_name="MPFAC-HIF-ES Error Peaks"
)
reference_mz = reference_peaks_df["m/z"].tolist() + error_peaks_df["m/z"].tolist()
reference_ccs = reference_peaks_df["CCS"].tolist() + error_peaks_df["CCS"].tolist()
# Initialize a DataFrame to collect all summary results
all_summaries = pd.DataFrame()


# Define the function to match with the external library and return all potential matches
def match_external_library(
    mz_value, library_masses, library_preferred_names, ppm_threshold=10
):
    matches = []
    for mass in library_masses:
        ppm_diff = abs(mz_value - mass) / mass * 1e6
        if ppm_diff < ppm_threshold:
            matches.append(library_preferred_names.get(mass))
    if matches:
        return ", ".join(matches)  # Join all matches as a single string
    return None


# Iterate over each CSV file found
for file_path in csv_files:
    # Load the CSV file
    df = pd.read_csv(file_path)
    start_time = time.time()  # Start timing the process

    # Convert the 'Name_or_Class' column to string to avoid AttributeError
    df["Name_or_Class"] = df["Name_or_Class"].astype(str)

    # Exclude rows where 'Name_or_Class' column contains '13C'
    df = df[~df["Name_or_Class"].str.contains("13C", na=False)]

    # Extract the number preceding .d from the file name for the header
    file_name = os.path.basename(file_path)
    header_name = file_name.split(".d")[0].split()[
        -1
    ]  # Extract the number for the header

    # Define the order of scores from best to worst
    score_order = [
        "A+",
        "A",
        "A-",
        "B+",
        "B",
        "B-",
        "C+",
        "C",
        "C-",
        "D+",
        "D",
        "D-",
        "E",
    ]

    # Filter rows based on the score being greater than 'E'
    filtered_df = df[
        df["Score"].apply(lambda x: score_order.index(x) <= score_order.index("E"))
    ]

    intensity_column = [col for col in df.columns if col.endswith(".DeMP")][0]

    # Function to eliminate rows with CCS difference less than 2% and m/z difference less than 10 ppm (eliminates branching in peaks we can't reasonably separate)
    def eliminate_close_rows(df):
        df = df.sort_values(by="m/z").reset_index(
            drop=True
        )  # Sort by m/z and reset index
        indices_to_keep = set(df.index)  # Keep all indices initially

        for i in range(len(df)):
            if i not in indices_to_keep:
                continue

            # Filter potential matches to reduce calculations
            potential_matches = df[
                (df["m/z"] > df.loc[i, "m/z"] - 0.01)
                & (df["m/z"] < df.loc[i, "m/z"] + 0.01)
            ]

            for j in potential_matches.index:
                if j <= i:
                    continue
                mz1 = df.loc[i, "m/z"]
                mz2 = df.loc[j, "m/z"]
                ccs1 = df.loc[i, "CCS"]
                ccs2 = df.loc[j, "CCS"]
                intensity1 = df.loc[i, intensity_column]
                intensity2 = df.loc[j, intensity_column]

                # Calculate ppm difference for m/z and percentage difference for CCS
                ppm_diff = abs(mz1 - mz2) / mz1 * 1e6
                ccs_diff = abs(ccs1 - ccs2) / ccs1 * 100

                if ppm_diff < 10 and ccs_diff < 2:
                    if intensity1 >= intensity2:
                        indices_to_keep.discard(j)
                    else:
                        indices_to_keep.discard(i)
                        break
        return df.loc[list(indices_to_keep)]

    # SMEAR FILTER - this is the big time - prevents larger peaks from smearing into the drift window of smaller peaks
    def eliminate_mass_shift_rows(df):
        df = df.sort_values("m/z").reset_index(drop=True)  # Sort by m/z and reset index
        indices_to_keep = set(df.index)  # Keep all indices initially

        for i in range(len(df)):
            if i not in indices_to_keep:
                continue
            mz1 = df.loc[i, "m/z"]
            ccs1 = df.loc[i, "CCS"]
            intensity1 = df.loc[i, intensity_column]
            retention_time1 = df.loc[
                i, "Retention Time"
            ]  # Get retention time of the first peak

            # Get potential matches to reduce calculations - this identifies things with a LOWER mass - selects the lower mass row as being i, the higher mass row as being j which is discarded if the conditions are met.
            potential_matches1 = df[
                (df["m/z"] >= mz1)
                & (df["m/z"] < mz1 + 2)
                & (abs(df["CCS"] - ccs1) / ccs1 * 100 < 2)
            ]

            for j in potential_matches1.index:
                if j <= i:
                    continue
                mz2 = df.loc[j, "m/z"]
                ccs2 = df.loc[j, "CCS"]
                intensity2 = df.loc[j, intensity_column]
                retention_time2 = df.loc[
                    j, "Retention Time"
                ]  # Get retention time of the second peak

                # Calculate ppm difference for a mass shift and percentage difference for CCS
                diff_mass_shift = abs(mz2 - mz1)
                ccs_diff = abs(ccs1 - ccs2) / ccs1 * 100
                intensity_diff = intensity1 / intensity2
                retention_time_diff = abs(retention_time1 - retention_time2)

                if (
                    diff_mass_shift < 2
                    and ccs_diff < 2
                    and intensity_diff > 50
                    and retention_time_diff < 0.5
                ):
                    indices_to_keep.discard(j)

            # "M+1" Filter for CCS within 2% and mass within +1.0 to +1.01 units - eliminates M+1 peaks
            for j in potential_matches1.index:
                if j <= i:
                    continue
                mz2 = df.loc[j, "m/z"]
                ccs2 = df.loc[j, "CCS"]
                retention_time2 = df.loc[j, "Retention Time"]
                retention_time_diff = abs(retention_time1 - retention_time2)

                # Calculate ppm difference for a mass shift and percentage difference for CCS
                diff_mass_shift = abs(mz1 - mz2)
                ccs_diff = abs(ccs1 - ccs2) / ccs1 * 100

                if (
                    1.0 <= diff_mass_shift <= 1.01
                    and ccs_diff < 2
                    and retention_time_diff < 0.25
                ):
                    indices_to_keep.discard(i)

        return df.loc[list(indices_to_keep)]

    filtered_df = eliminate_close_rows(filtered_df)
    filtered_df = eliminate_mass_shift_rows(filtered_df)

    def remove_reference_rows(df, reference_mz, reference_ccs):
        df = df.reset_index(drop=True)  # Reset index to ensure iloc works correctly
        indices_to_remove = set()
        for i in range(len(df)):
            mz = df.iloc[i]["m/z"]
            ccs = df.iloc[i]["CCS"]
            for ref_mz, ref_ccs in zip(reference_mz, reference_ccs):
                ppm_diff = abs(mz - ref_mz) / ref_mz * 1e6
                ccs_diff = abs(ccs - ref_ccs) / ref_ccs * 100
                if ppm_diff < 10 and ccs_diff < 2:
                    indices_to_remove.add(i)
                    break
        return df.drop(list(indices_to_remove))

    def neutral_losses(df, neutral_loss_masses, ppm_tolerance=10):
        # Sort DataFrame by m/z and reset index
        df = df.sort_values(by="m/z").reset_index(drop=True)

        # Set to keep track of rows to retain
        indices_to_keep = set(df.index)

        # Iterate over each row in the DataFrame
        for i in range(len(df)):
            if i not in indices_to_keep:
                continue  # Skip if the row has already been excluded
            if df.loc[i, "Score"] in ["E"]:
                continue  # Skip this row if the score is 'E or A'
            mz1 = df.loc[i, "m/z"]
            RT1 = df.loc[i, "Retention Time"]

            # Iterate over potential matches where mass j is greater than mass i
            for j in range(i + 1, len(df)):
                mz2 = df.loc[j, "m/z"]
                RT2 = df.loc[j, "Retention Time"]

                # Ensure the retention time difference is within the tolerance (0.2 minutes)
                RT_diff = abs(RT1 - RT2)
                if RT_diff > 0.1 and mz2 - mz1 > 100:
                    continue  # Skip if retention times differ too much

                # Calculate the mass difference (j - i)
                mass_difference = abs(mz2 - mz1)

                # Check if the mass difference matches any of the neutral loss masses
                for neutral_mz in neutral_loss_masses:
                    ppm_diff = abs((mass_difference - neutral_mz) / neutral_mz) * 1e6
                    if ppm_diff <= ppm_tolerance:
                        # If a match is found, discard row i (the smaller mass)
                        indices_to_keep.discard(i)
                        break  # Stop checking once we find a match for this pair

        # Return the filtered DataFrame with only the indices that were not discarded
        return df.loc[list(indices_to_keep)].reset_index(drop=True)

    def adducts_and_n_mers(df):
        # Sort DataFrame by m/z and reset index
        df = df.sort_values(by="m/z").reset_index(drop=True)

        # Set to keep track of rows to retain
        indices_to_keep = set(df.index)

        # Iterate over each row in the DataFrame
        for i in range(len(df)):
            if i not in indices_to_keep:
                continue  # Skip if the row has already been excluded
            if df.loc[i, "Score"] == "E":
                continue  # Skip if the score is 'E'

            mz1 = df.loc[i, "m/z"]
            RT1 = df.loc[i, "Retention Time"]

            # Iterate over potential matches where mass j is greater than mass i
            for j in range(i + 1, len(df)):
                mz2 = df.loc[j, "m/z"]
                RT2 = df.loc[j, "Retention Time"]

                # Ensure the retention time difference is within 0.2 minutes
                RT_diff = abs(RT1 - RT2)
                if RT_diff > 0.2:
                    continue  # Skip if retention times differ too much

                # Check the three conditions
                if abs(mz2 - (mz1 + 21.981945)) <= 0.01:
                    indices_to_keep.discard(j)  # Exclude j if j = i + 21.981945
                    continue

                if abs(mz2 - (2 * mz1 + 1.007825)) <= 0.01:
                    indices_to_keep.discard(j)  # Exclude j if j = 2i + 1.007825
                    continue

                if abs(mz2 - (2 * mz1 + 21.981945)) <= 0.01:
                    indices_to_keep.discard(j)  # Exclude j if j = 2i + 21.981945
                    continue

        # Return the filtered DataFrame with only the indices that were not discarded
        return df.loc[list(indices_to_keep)].reset_index(drop=True)

    # Apply the removal of reference rows
    filtered_df = remove_reference_rows(filtered_df, reference_mz, reference_ccs)
    filtered_df = adducts_and_n_mers(filtered_df)

    # Final filter to remove rows scored as E - only now are the "non-PFAS" features eliminated - ensures any biomolecule junk that may interfere with signal is considered by the smear filter
    filtered_df = filtered_df[~filtered_df["Score"].isin(["E"])]
    # Fluorinated ML algorithm separation line to eliminate features with abnormally high CCS to m/z values
    filtered_df = filtered_df[
        filtered_df.apply(lambda row: row["m/z"] * 0.19 + 110.28 > row["CCS"], axis=1)
    ]

    # Separate tentative rows for EPA matching
    tentative_df = filtered_df[
        filtered_df["Score"].isin(["B+", "B", "B-", "C+", "C", "C-", "D-", "D", "D+"])
    ].copy()

    # Perform EPA matching on tentative matches and collect all possible matches - if there are instances where multiple targets match with a given mass, all matches are given, separated by a /
    def match_multiple_library_names(
        mz_value, library_masses, library_preferred_names, ppm_threshold=10
    ):
        matches = []
        for mass in library_masses:
            ppm_diff = abs(mz_value - mass) / mass * 1e6
            if ppm_diff < ppm_threshold:
                matches.append(library_preferred_names.get(mass))
        return "/".join(matches) if matches else None

    tentative_df.loc[:, "EPA_Match"] = tentative_df["m/z"].apply(
        lambda mz: match_multiple_library_names(
            mz, library_masses, library_preferred_names
        )
        is not None
    )

    # Update 'Name_or_Class' with all potential matches if they exist
    tentative_df.loc[:, "Name_or_Class"] = tentative_df.apply(
        lambda row: match_multiple_library_names(
            row["m/z"], library_masses, library_preferred_names
        )
        or row["Name_or_Class"],
        axis=1,
    )

    # Classify rows based on score
    def classify_score(row):
        if row in ["A+", "A", "A-"]:
            return "likely"
        elif row in ["B+", "B", "B-", "C+", "C", "C-", "D-", "D", "D+"]:
            return "tentative"
        return None

    filtered_df["Classification"] = filtered_df["Score"].apply(classify_score)

    # Split filtered_df into likely and tentative dataframes
    likely_df = filtered_df[filtered_df["Classification"] == "likely"]
    tentative_df_with_match = tentative_df[tentative_df["EPA_Match"]]
    tentative_df_without_match = tentative_df[~tentative_df["EPA_Match"]]

    # Additional filtering step: for the "Tentative (No EPA match)" category,
    # remove rows where multiple rows within 10 ppm exist, keeping the row with the lowest CCS - "look down" CCS filter - designed to eliminate the influence of dimers etc. by chosing the peak with the lowest CCS for a given mass
    def filter_within_10ppm(df):
        df = df.sort_values(by=["m/z", "CCS"]).reset_index(drop=True)
        indices_to_keep = set()
        for i in range(len(df)):
            mz1 = df.loc[i, "m/z"]

            potential_matches = df[(abs(df["m/z"] - mz1) <= 0.01)]
            if not potential_matches.empty:
                # Keep the row with the lowest CCS for the current group
                min_ccs_row = potential_matches.loc[potential_matches["CCS"].idxmin()]
                indices_to_keep.add(min_ccs_row.name)

        # Convert the set to a list for indexing
        return df.loc[list(indices_to_keep)]

    # Apply the filtering for "Tentative (No EPA match)"
    filtered_no_match_df = filter_within_10ppm(tentative_df_without_match)

    # Count the number of likely, tentative with EPA match, and tentative without EPA match
    likely_count = likely_df.shape[0]
    tentative_with_match_count = tentative_df_with_match.shape[0]
    tentative_without_match_count = filtered_no_match_df.shape[0]

    # Print the counts for this file
    print(f"File: {header_name}")
    print(f"Likely: {likely_count}")
    print(f"Tentative (EPA library match): {tentative_with_match_count}")
    print(f"Tentative (No library match): {tentative_without_match_count}")

    # Convert classification counts to a DataFrame and transpose to have "likely" and "tentative" as rows
    summary_df = pd.DataFrame(
        {
            "Likely": [likely_count],
            "Tentative (EPA library match)": [tentative_with_match_count],
            "Tentative (No library match)": [tentative_without_match_count],
        }
    )
    summary_df.insert(0, "Header", header_name)  # Insert the header as the first column

    # Append the summary to the all_summaries DataFrame
    all_summaries = pd.concat([all_summaries, summary_df], axis=0)

    # Define the output path for the filtered data
    filtered_output_path = os.path.join(
        directory_path, f"{header_name}_fluoromatch_processed.xlsx"
    )
    directory_path2 = r"F:\Twins Project (2.24-)\Non-target work\All Features Master"
    filtered_output_path2 = os.path.join(
        directory_path2, f"{header_name}_fluoromatch_processed.xlsx"
    )

    # Save the filtered data to a new Excel file with three sheets: likely, tentative_with_match, tentative_without_match
    with pd.ExcelWriter(filtered_output_path) as writer:
        likely_df.to_excel(writer, sheet_name="Likely", index=False)
        tentative_df_with_match.to_excel(
            writer, sheet_name="Tentative (EPA match)", index=False
        )
        filtered_no_match_df.to_excel(
            writer, sheet_name="Tentative (No EPA match)", index=False
        )
    with pd.ExcelWriter(filtered_output_path2) as writer:
        likely_df.to_excel(writer, sheet_name="Likely", index=False)
        tentative_df_with_match.to_excel(
            writer, sheet_name="Tentative (EPA match)", index=False
        )
        filtered_no_match_df.to_excel(
            writer, sheet_name="Tentative (No EPA match)", index=False
        )
    print(f"Filtered data saved to {filtered_output_path}.")
    elapsed_time = time.time() - start_time
    print(f"{elapsed_time:.1f} seconds")
# Define the output path for the combined summary spreadsheet - spits a summary of the count for each file you hand it
summary_output_path = os.path.join(directory_path, "Classification_Summary.xlsx")

# Save the combined summary data to a new Excel file
all_summaries.to_excel(summary_output_path, index=False)

print(f"Combined summary saved to {summary_output_path}.")
