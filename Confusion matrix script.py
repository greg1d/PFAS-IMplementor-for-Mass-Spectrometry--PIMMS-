import os
import re
import pandas as pd

# File paths
true_data_path = r"F:\Twins Project (2.24-)\Non-target work\Model development\9Cl-PF3ONS (Skyline).xlsx"
results_folder = r"F:\Twins Project (2.24-)\Non-target work\Model development\results\practice"

# Create an empty DataFrame to store results
result_data = []

# Function to extract only the numeric part of the filename
def extract_numeric_part(filename):
    match = re.search(r'\d+', filename)
    return match.group(0) if match else filename

# Function to check if '9Cl-PF3ONS' is in the "Name_or_Class" column of the "Likely" sheet
def check_9Cl_PF3ONS_in_file(file_path):
    try:
        # Read the Likely sheet
        df = pd.read_excel(file_path, sheet_name="Likely")
        # Check if '9Cl-PF3ONS' is present in the 'Name_or_Class' column
        if df['Name_or_Class'].str.contains('9Cl-PF3ONS', na=False).any():
            return 1
        else:
            return 0
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None  # For cases where the file or sheet does not exist

# Loop through all files in the results folder
for root, dirs, files in os.walk(results_folder):
    for file in files:
        if file.endswith(".xlsx"):
            file_path = os.path.join(root, file)
            result = check_9Cl_PF3ONS_in_file(file_path)
            if result is not None:
                numeric_part = extract_numeric_part(file)
                result_data.append({"File": numeric_part, "9Cl-PF3ONS_Present": result})

# Convert results to a DataFrame
result_df = pd.DataFrame(result_data)

# Save the results to an Excel file
output_path = r"F:\Twins Project (2.24-)\Non-target work\Model development\9Cl_PF3ONS_results.xlsx"
result_df.to_excel(output_path, index=False)

print(f"Results saved to {output_path}")
