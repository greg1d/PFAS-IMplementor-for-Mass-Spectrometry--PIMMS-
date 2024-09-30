import pandas as pd
import os
import glob

# Define the directory containing the Excel files
directory_path = r'F:\Twins Project (2.24-)\Non-target work\Dummy results for Anna'

# Find all Excel files in the directory that end with "fluoromatch_processed.xlsx"
excel_files = glob.glob(os.path.join(directory_path, '*fluoromatch_processed.xlsx'))

# Initialize an empty dictionary to store the chemical counts
chemical_counts = {}

# Function to process each 'Name_or_Class' entry and update the chemical counts
def process_chemicals(chemicals_str, unique_chemicals_in_file):
    # Check if there are multiple chemicals (indicated by '/')
    if '/' in chemicals_str:
        # Split by '/' and add '*' to each chemical, then join them back
        chemicals = [chem.strip() + '*' for chem in chemicals_str.split('/')]
    else:
        # If there's only one chemical, keep it as it is
        chemicals = [chemicals_str.strip()]

    # Remove duplicates in the same file
    unique_chemicals = set(chemicals)

    # Update the chemical counts dictionary but only if the chemical hasn't been counted in the current file
    for chemical in unique_chemicals:
        if chemical not in unique_chemicals_in_file:
            unique_chemicals_in_file.add(chemical)  # Mark this chemical as counted for this file
            if chemical in chemical_counts:
                chemical_counts[chemical] += 1
            else:
                chemical_counts[chemical] = 1

# Iterate over each Excel file found
for file_path in excel_files:
    print(f"Processing file: {file_path}")
    
    # Initialize a set to track chemicals counted in the current file
    unique_chemicals_in_file = set()
    
    # Load the sheet "Tentative (EPA match)"
    try:
        df = pd.read_excel(file_path, sheet_name='Tentative (EPA match)')
        
        # Check if the 'Name_or_Class' column exists in the sheet
        if 'Name_or_Class' in df.columns:
            # Process each row in the 'Name_or_Class' column
            df['Name_or_Class'].dropna().apply(lambda x: process_chemicals(x, unique_chemicals_in_file))  # Drop NaN values and process the chemicals
        else:
            print(f"'Name_or_Class' column not found in {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Calculate the number of files processed
num_files = len(excel_files)

# Convert the chemical counts dictionary to a DataFrame for better readability
chemical_counts_df = pd.DataFrame(list(chemical_counts.items()), columns=['Chemical', 'Count'])

# Add a new column for detection frequency (Count divided by number of files)
chemical_counts_df['Detection Frequency'] = chemical_counts_df['Count'] / num_files

# Sort the DataFrame by the count in descending order
chemical_counts_df = chemical_counts_df.sort_values(by='Count', ascending=False)

# Define the output path for the results within the same directory
output_path = os.path.join(directory_path, 'chemical_detection_summary_with_frequency.xlsx')

# Save the results to a new Excel file in the same directory
chemical_counts_df.to_excel(output_path, index=False)

print(f"Chemical detection summary with detection frequency saved to {output_path}")
