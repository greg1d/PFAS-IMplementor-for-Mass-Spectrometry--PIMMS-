import pandas as pd
import sys
import os

# Add the path to the modules folder if it's not already in sys.path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
if module_path not in sys.path:
    sys.path.append(module_path)

from Standard_library_scoring import find_similar_peaks, load_pfas_library


def import_likely_rows(file_path):
    """
    Reads the specified CSV file and imports rows where 'Classification Type' is 'likely'.
    """
    try:
        # Read the CSV file
        data = pd.read_csv(file_path)

        # Filter rows where 'Classification Type' is 'likely'
        filtered_data = data[data["Classification Type"] == "likely"]

        # Process the filtered rows (import or further operations can be added here)
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
    file_path = r"f:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    likely_df = import_likely_rows(file_path)

    # ✅ Confirm import of function
    print("Function imported successfully:", find_similar_peaks)

    mass_error_ppm = 10
    rt_tolerance = 2.0
    ccs_tolerance = 2.0
    include_rt = False

    # ✅ Load PFAS library
    standards_library_file = r"f:\PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-\PIMMS v1.2\import folder\Standards Library\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    try:
        pfas_library = load_pfas_library(standards_library_file)
        print("PFAS Library loaded successfully. First 5 rows:")
        print(pfas_library.head())
    except Exception as e:
        print(f"Error loading PFAS library: {e}")
        pfas_library = None

    # ✅ Run similarity matching
    if likely_df is not None and pfas_library is not None:
        try:
            matched_df = find_similar_peaks(likely_df, pfas_library)
            print("Similarity matching complete. First 5 rows of result:")
            print(matched_df.head())
        except Exception as e:
            print(f"Error during similarity matching: {e}")
