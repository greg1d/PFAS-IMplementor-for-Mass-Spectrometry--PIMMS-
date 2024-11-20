import os
import shutil

import pandas as pd

# File paths
organization_sheet = r"F:\Twins Project (2.24-)\Non-target work\Year organizing script\Year catagorization for samples.xlsx"
unsorted_folder = r"F:\Twins Project (2.24-)\Non-target work\Year organizing script\Organized\Unsorted raw"
sorted_folder_base = r"F:\Twins Project (2.24-)\Non-target work\Year organizing script\Organized\organized by year"

# Load the year categorization file
year_data = pd.read_excel(organization_sheet)

# Create folders based on year and copy the files
for _, row in year_data.iterrows():
    sample_name = str(row["Sample"])  # Sample number
    year = str(row["Visit Date Year"])  # Year

    # Create a folder for each year (e.g., 2005, 2006)
    year_folder = os.path.join(sorted_folder_base, year)
    if not os.path.exists(year_folder):
        os.makedirs(year_folder)

    # Find the corresponding file in the unsorted folder
    for file in os.listdir(unsorted_folder):
        # Ensure exact matching by checking if the filename starts with the sample number followed by a delimiter
        if file.startswith(f"{sample_name}_") or file.startswith(f"{sample_name} "):
            src_file = os.path.join(unsorted_folder, file)
            dest_file = os.path.join(year_folder, file)
            # Copy the file to the correct folder
            shutil.copy(src_file, dest_file)
            print(f"Copied {file} to {year_folder}")
            break

print("Files have been copied and organized by individual years.")
