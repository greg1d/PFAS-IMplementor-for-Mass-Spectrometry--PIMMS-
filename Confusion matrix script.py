import os
import re

import pandas as pd
from sklearn.metrics import confusion_matrix

# File paths
true_data_path = r"F:\Twins Project (2.24-)\Non-target work\Model development\9Cl-PF3ONS (Skyline).xlsx"
results_folder = (
    r"F:\Twins Project (2.24-)\Non-target work\Model development\Results\Full Data Set"
)

# Create an empty DataFrame to store results
result_data = []


# Function to extract only the numeric part of the sample names (e.g., "7292" from "303 B4 7292")
def extract_sample_number(sample_name):
    match = re.search(r"\d+$", sample_name)
    return match.group(0) if match else None


# Function to extract only the numeric part of the filename
def extract_numeric_part(filename):
    match = re.search(r"\d+", filename)
    return match.group(0) if match else filename


# Function to check if '9Cl-PF3ONS' is in the "Name_or_Class" column of the "Likely" sheet
def check_9Cl_PF3ONS_in_file(file_path):
    try:
        # Read the Likely sheet
        df = pd.read_excel(file_path, sheet_name="Likely")
        # Check if '9Cl-PF3ONS' is present in the 'Name_or_Class' column
        if df["Name_or_Class"].str.contains("9Cl-PF3ONS", na=False).any():
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
                result_data.append(
                    {"Sample": numeric_part, "9Cl-PF3ONS_Present": result}
                )

# Convert results to a DataFrame
result_df = pd.DataFrame(result_data)

# Load the true data (Skyline) file
true_data_df = pd.read_excel(true_data_path)

# Extract sample number from the "Sample Name" column in the true data
true_data_df["Sample"] = true_data_df["Sample"].apply(extract_sample_number)

# Merge the true data with the model result data on the sample number
merged_df = pd.merge(
    true_data_df[["Sample", "Presence"]], result_df, on="Sample", how="left"
)

# Drop rows where there is no entry from the results folder (NaN in '9Cl-PF3ONS_Present')
merged_df.dropna(subset=["9Cl-PF3ONS_Present"], inplace=True)

# Rename columns for better clarity
merged_df.rename(
    columns={"Presence": "Skyline", "9Cl-PF3ONS_Present": "Model"}, inplace=True
)

# Calculate confusion matrix using only the valid data
y_true = merged_df["Skyline"].astype(int)
y_pred = merged_df["Model"].astype(int)
tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

# Print the confusion matrix and Type I / Type II errors
print(
    f"Confusion Matrix:\n[[TN: {tn}, FP (Type I Error): {fp}]\n[FN (Type II Error): {fn}, TP: {tp}]]"
)
print(f"\nType I errors (False Positives): {fp}")
print(f"Type II errors (False Negatives): {fn}")

# Save the merged results with confusion matrix data to an Excel file
output_path = r"F:\Twins Project (2.24-)\Non-target work\Model development\9Cl_PF3ONS_comparison_results_with_confusion.xlsx"
merged_df.to_excel(output_path, index=False)

print(f"Comparison results with confusion matrix saved to {output_path}")
