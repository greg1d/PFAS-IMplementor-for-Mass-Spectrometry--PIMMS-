import pandas as pd
import os
import glob

# Define the directory containing the Excel files
directory_path = r'F:\Twins Project (2.24-)\Non-target work\All Features Master'

# Define the directory to save the search results
output_directory = r'F:\Twins Project (2.24-)\Non-target work\All Features Master\Search Results'
os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn't exist

# Find all Excel files in the directory
excel_files = glob.glob(os.path.join(directory_path, '*.xlsx'))

# Define a mapping for sheet options
sheet_mapping = {
    1: 'Likely',
    2: 'Tentative (EPA match)',
    3: 'Tentative (No EPA match)'
}

# Function to perform the search with ppm error for m/z and Name_or_Class search
def search_feature(name_or_class=None, mz_value=None, ppm_error=10, sheet_options=None):
    results = []
    
    # Iterate over each Excel file found
    for file_path in excel_files:
        for sheet_option in sheet_options:
            sheet_name = sheet_mapping.get(sheet_option, None)
            
            if not sheet_name:
                print(f"Invalid sheet option: {sheet_option}. Skipping...")
                continue
            
            print(f"Searching in file: {file_path}, Sheet: {sheet_name}")
            
            # Try loading the specified sheet
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Find columns that match specific criteria
                ccs_column = 'CCS'
                retention_time_column = 'Retention Time'
                demp_column = next((col for col in df.columns if col.endswith('.d.DeMP')), None)
                
                # Ensure the necessary columns exist
                if not ccs_column in df.columns or not retention_time_column in df.columns or demp_column is None:
                    print(f"Missing required columns in {file_path} (Sheet: {sheet_name}), skipping this sheet.")
                    continue

                # If m/z search is provided, calculate the ppm error range
                if mz_value is not None:
                    mz_min = mz_value - (mz_value * ppm_error / 1e6)
                    mz_max = mz_value + (mz_value * ppm_error / 1e6)
                    mz_match = df[(df['m/z'] >= mz_min) & (df['m/z'] <= mz_max)]
                else:
                    mz_match = df  # If m/z is not specified, consider all rows

                # If Name_or_Class search is provided, further filter the result
                if name_or_class is not None:
                    # Use .str.contains with regex=False to avoid issues with names that start with numbers
                    mz_match = mz_match[mz_match['Name_or_Class'].str.contains(name_or_class, na=False, case=False, regex=False)]

                # If any matches are found, store them along with the file and sheet information
                if not mz_match.empty:
                    for _, row in mz_match.iterrows():
                        results.append({
                            'File': os.path.basename(file_path),
                            'Sheet': sheet_name,
                            'Name_or_Class': row.get('Name_or_Class', 'N/A'),
                            'm/z': row.get('m/z', 'N/A'),
                            'CCS': row.get(ccs_column, 'N/A'),
                            'Retention Time': row.get(retention_time_column, 'N/A'),
                            'Intensity': row.get(demp_column, 'N/A'),  # Renamed from DeMP Value to Intensity
                            'Other Data': row.to_dict()  # Include all other row data if needed
                        })
            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
    
    # Convert results to DataFrame for better readability
    if results:
        result_df = pd.DataFrame(results)
        # Sort the results by Intensity in descending order
        result_df = result_df.sort_values(by='Intensity', ascending=False)
        print(result_df)
        
        # Ask the user if they want to save the results
        save_option = input("Do you want to save the results to an Excel file? (yes/no): ").strip().lower()
        if save_option == 'yes':
            file_name = input("Enter a name for the output file (without extension): ").strip()
            output_file_path = os.path.join(output_directory, f"{file_name}.xlsx")
            result_df.to_excel(output_file_path, index=False)
            print(f"Results saved to {output_file_path}")
        
        return result_df
    else:
        print("No matches found.")
        return None

# Function to initiate a search loop until the user wants to stop
def search_loop():
    while True:
        # User input to specify search criteria
        search_name_or_class = input("Enter the Name_or_Class to search (leave blank to skip): ")
        search_mz_value = input("Enter the m/z value to search (leave blank to skip): ")

        # Convert m/z value to float if provided
        search_mz_value = float(search_mz_value) if search_mz_value else None

        # User input to specify the sheets to search
        print("Enter the sheets to search (1 - Likely, 2 - Tentative (EPA Match), 3 - Tentative (No EPA Match)).")
        print("You can select multiple sheets by entering their numbers separated by space (e.g., '1 2 3').")
        sheet_input = input("Select sheet(s): ")
        sheet_options = list(map(int, sheet_input.split()))

        # Perform the search across multiple sheets
        search_feature(name_or_class=search_name_or_class, mz_value=search_mz_value, sheet_options=sheet_options)
        
        # Ask the user if they want to search again
        continue_search = input("Do you want to perform another search? (yes/no): ").strip().lower()
        if continue_search != 'yes':
            print("Exiting the search.")
            break

# Start the search loop
search_loop()
