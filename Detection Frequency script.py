import pandas as pd
import os
import glob
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# Define the directory containing the Excel files
directory_path = r'F:\Twins Project (2.24-)\Non-target work\2003-2004 test'

# Find all Excel files in the directory that end with "fluoromatch_processed.xlsx"
excel_files = glob.glob(os.path.join(directory_path, '*fluoromatch_processed.xlsx'))

# Initialize an empty dictionary to store the chemical counts and CCS/RT data
chemical_counts = {}
chemical_data = {}

# Function to process each 'Name_or_Class' entry and update the chemical counts
def process_chemicals(chemicals_str, ccs, rt, file_name, unique_chemicals_in_file):
    if '/' in chemicals_str:
        chemicals = [chem.strip() + '*' for chem in chemicals_str.split('/')]
    else:
        chemicals = [chemicals_str.strip()]

    unique_chemicals = set(chemicals)

    for chemical in unique_chemicals:
        if chemical not in unique_chemicals_in_file:
            unique_chemicals_in_file.add(chemical)
            if chemical in chemical_counts:
                chemical_counts[chemical] += 1
            else:
                chemical_counts[chemical] = 1

        # Store CCS and RT values for each file
        if chemical not in chemical_data:
            chemical_data[chemical] = {}
        chemical_data[chemical][file_name + ' CCS'] = f"{ccs:.1f}"
        chemical_data[chemical][file_name + ' RT'] = f"{rt:.1f}"

# Iterate over each Excel file found
for file_path in excel_files:
    file_name = os.path.basename(file_path).replace('_fluoromatch_processed.xlsx', '')  # Extract the file name without extension
    print(f"Processing file: {file_path}")
    
    unique_chemicals_in_file = set()
    
    try:
        df = pd.read_excel(file_path, sheet_name='Tentative (EPA match)')
        
        if 'Name_or_Class' in df.columns and 'CCS' in df.columns and 'Retention Time' in df.columns:
            df.dropna(subset=['Name_or_Class']).apply(lambda row: process_chemicals(row['Name_or_Class'], row['CCS'], row['Retention Time'], file_name, unique_chemicals_in_file), axis=1)
        else:
            print(f"Required columns ('Name_or_Class', 'CCS', 'Retention Time') not found in {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Calculate the number of files processed
num_files = len(excel_files)

# Convert the chemical counts dictionary to a DataFrame
chemical_counts_df = pd.DataFrame(list(chemical_counts.items()), columns=['Chemical', 'Count'])

# Add a new column for detection frequency (Count divided by number of files)
chemical_counts_df['Detection Frequency'] = chemical_counts_df['Count'] / num_files

# Convert the chemical data dictionary to a DataFrame for the CCS and RT values
chemical_data_df = pd.DataFrame.from_dict(chemical_data, orient='index')

# Merge the chemical counts DataFrame with the chemical data DataFrame
final_df = pd.merge(chemical_counts_df, chemical_data_df, left_on='Chemical', right_index=True, how='left')
final_df = final_df.sort_values(by='Detection Frequency', ascending=False)

# Calculate mean and standard deviation of CCS and RT columns
ccs_cols = [col for col in final_df.columns if 'CCS' in col]
rt_cols = [col for col in final_df.columns if 'RT' in col]

z_scores = {}  # Dictionary to hold Z-scores for each column

for col in ccs_cols + rt_cols:
    col_values = pd.to_numeric(final_df[col], errors='coerce')  # Convert to numeric
    col_mean = col_values.mean()
    col_std = col_values.std()

    # Calculate Z-scores and store them in the dictionary
    z_scores[col] = (col_values - col_mean) / col_std

# Define the output path for the results
output_path = os.path.join(directory_path, 'chemical_detection_summary_with_ccs_rt_and_frequency.xlsx')

# Save the results to a new Excel file
final_df.to_excel(output_path, index=False)

# Load the saved Excel file to apply conditional formatting
wb = load_workbook(output_path)
ws = wb.active

# Define red fill for highlighting
red_fill = PatternFill(start_color='FF6666', end_color='FF6666', fill_type='solid')

# Apply Z-score highlighting directly to the CCS and RT columns based on calculated Z-scores
for col in ccs_cols + rt_cols:
    z_score_col = z_scores[col]
    for row_idx, z_score in enumerate(z_score_col, start=2):  # Start at 2 because Excel rows are 1-indexed
        if pd.notna(z_score) and abs(z_score) > 2:
            cell = ws.cell(row=row_idx, column=final_df.columns.get_loc(col) + 1)  # Get the correct column index
            cell.fill = red_fill  # Apply the red fill for Z-scores greater than 2

# Save the workbook with the applied conditional formatting
wb.save(output_path)

print(f"Chemical detection summary with CCS, Retention Time, and detection frequency saved to {output_path}")
