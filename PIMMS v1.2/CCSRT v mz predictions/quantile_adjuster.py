import pandas as pd
import sys
import os
import re  # Importing the regex module

# Add the path to the modules folder if it's not already in sys.path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
if module_path not in sys.path:
    sys.path.append(module_path)

from Standard_library_scoring import find_similar_peaks, load_pfas_library


# Function to remove anything within parentheses (including the parentheses)
def remove_brackets(text):
    """Remove anything inside parentheses and the parentheses themselves."""
    return re.sub(r"\s*\(.*?\)\s*", "", text)


# Function to calculate RT error
def calculate_rt_error(likely_rt, pfas_rt):
    """Calculates the absolute RT error between the likely and PFAS library values."""
    return abs(likely_rt - pfas_rt)


# Import likely rows from the CSV
def import_likely_rows(file_path):
    """
    Reads the specified CSV file and imports rows where 'Classification Type' is 'likely'.
    """
    try:
        # Read the CSV file
        data = pd.read_csv(file_path)

        # Filter rows where 'Classification Type' is 'likely'
        filtered_data = data[data["Classification Type"] == "likely"]

        # Apply the remove_brackets function to the 'Match' column
        filtered_data["Match"] = filtered_data["Match"].apply(remove_brackets)

        # Process the filtered rows
        print(
            f"Imported {len(filtered_data)} rows where 'Classification Type' is 'likely'."
        )
        return filtered_data
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except KeyError:
        print("Error: The column 'Classification Type' does not exist in the file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage
if __name__ == "__main__":
    file_path = r"f:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS v1.2\Data_output\PIMMS Processed Data set for testing.csv"
    likely_df = import_likely_rows(file_path)

    # ✅ Confirm import of function
    print("Function imported successfully:", find_similar_peaks)

    # ✅ Load PFAS library
    standards_library_file = r"f:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS v1.2\import folder\Standards Library\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    try:
        pfas_library = load_pfas_library(standards_library_file)
        print("PFAS Library loaded successfully. First 5 rows:")
        print(pfas_library.head())
    except Exception as e:
        print(f"Error loading PFAS library: {e}")
        pfas_library = None

    # ✅ Find similar peaks based on the "Match" column and calculate RT error
    if likely_df is not None and pfas_library is not None:
        try:
            # Apply the remove_brackets function to the 'PrecursorName' column in PFAS library
            pfas_library["PrecursorName"] = pfas_library["PrecursorName"].apply(
                remove_brackets
            )

            # Extract the 'Match' and RT values from likely_df
            likely_matches = likely_df["Match"].values
            likely_rts = likely_df["RT"].values

            # Extract the 'PrecursorName' and RT values from pfas_library
            pfas_names = pfas_library["PrecursorName"].values
            pfas_rts = dict(
                zip(pfas_library["PrecursorName"], pfas_library["PrecursorRT"])
            )

            # Loop through each Match in likely_df and find corresponding PrecursorName in pfas_library
            for match, rt in zip(likely_matches, likely_rts):
                if match in pfas_names:
                    pfas_rt = pfas_rts[match]
                    rt_error = calculate_rt_error(rt, pfas_rt)
                    print(
                        f"Matching precursor for '{match}' has RT error: {rt_error} (likely RT: {rt}, PFAS RT: {pfas_rt})"
                    )
                else:
                    print(f"No matching precursor found for '{match}'")
        except Exception as e:
            print(f"Error during RT error calculation: {e}")
