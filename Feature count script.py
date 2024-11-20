import os

import pandas as pd

# Directory containing the fluoromatch processed CSV files
directory_path = (
    r"F:\Twins Project (2.24-)\Non-target work\Processed Data\New method\2003-2004"
)

# Initialize an empty list to store summary data
summary_data = []

# Iterate over all files in the directory
for file in os.listdir(directory_path):
    if file.endswith("_fluoromatch_processed.xlsx"):  # Only process fluoromatch files
        file_path = os.path.join(directory_path, file)
        header_name = os.path.splitext(file)[0]  # Use the file name as the header

        # Load the Excel file
        xls = pd.ExcelFile(file_path)

        # Read the Likely, Tentative (EPA library match), and Tentative (No library match) sheets
        likely_df = pd.read_excel(xls, sheet_name="Likely")
        tentative_df_with_match = pd.read_excel(xls, sheet_name="Tentative (EPA match)")
        tentative_df_without_match = pd.read_excel(
            xls, sheet_name="Tentative (No EPA match)"
        )

        # Count the number of detections in each sheet
        likely_count = likely_df.shape[0]
        tentative_with_match_count = tentative_df_with_match.shape[0]
        tentative_without_match_count = tentative_df_without_match.shape[0]

        # Print the counts for this file (optional for debugging)
        print(f"File: {header_name}")
        print(f"Likely: {likely_count}")
        print(f"Tentative (EPA match): {tentative_with_match_count}")
        print(f"Tentative (No EPA match): {tentative_without_match_count}")

        # Append the classification counts to the summary_data list
        summary_data.append(
            {
                "Header": header_name,
                "Likely": likely_count,
                "Tentative (EPA match)": tentative_with_match_count,
                "Tentative (No EPA match)": tentative_without_match_count,
            }
        )

# Convert the summary_data list into a DataFrame
summary_df = pd.DataFrame(summary_data)

# Export the summary DataFrame to a CSV file
output_path = os.path.join(directory_path, "classification_summary.csv")
summary_df.to_csv(output_path, index=False)

print(f"Classification summary saved to {output_path}")
