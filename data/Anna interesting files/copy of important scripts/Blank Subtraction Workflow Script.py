import pandas as pd

# Load the Excel file
file_path = r"D:\2023 gators\PIMMS data\PIMMS Processing\All features.xlsx"
df = pd.read_excel(file_path)

# Identify sample and blank columns
sample_columns = [col for col in df.columns if ".d.DeMP" in col]
blank_columns = [col for col in df.columns if "Blank" in col]

# Metadata columns to keep
metadata_columns = [
    "ID",
    "RT",
    "DT",
    "CCS",
    "m/z",
    "Z",
    "Ions",
    "Freq.",
    "Q Score",
    "Sat.",
    "Mark",
]

# Initialize a DataFrame to store subtraction values for debugging
subtraction_values = pd.DataFrame(
    index=df.index, columns=["Mean_Blank", "Std_Blank", "Subtraction_Value"]
)

# Perform blank subtraction row-wise
for index, row in df.iterrows():
    # Calculate mean and std for blank values in the current row
    mean_blank = row[blank_columns].mean()
    std_blank = row[blank_columns].std()
    subtraction_value = mean_blank + 3 * std_blank

    # Store subtraction values for debugging
    subtraction_values.loc[index] = [mean_blank, std_blank, subtraction_value]

    # Subtract the calculated value from each sample column in the current row
    for sample_col in sample_columns:
        df.at[index, sample_col] -= subtraction_value

# Export each sample column along with metadata columns to a new CSV
for sample_col in sample_columns:
    # Combine sample column with metadata
    output_df = df[metadata_columns + [sample_col]]

    # Remove rows with negative values in the sample column
    output_df = output_df[output_df[sample_col] > 0]

    # Define the output file name
    output_file_name = f"{sample_col}_blank_subtracted.csv"

    # Save the DataFrame to a CSV file
    output_df.to_csv(output_file_name, index=False)

    print(f"Exported {output_file_name}")

print("All sample columns have been processed and exported.")
