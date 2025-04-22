from heavy_halogen_hunter import run_heavy_halogen_kaufman_pipeline
from CEF_matching_algorithm import match_PIMMS_to_CEF
import pandas as pd


def main():
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder_test"
    pimms_file = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
    all_matches = run_heavy_halogen_kaufman_pipeline(cef_folder, pimms_file)

    matches = match_PIMMS_to_CEF(cef_folder, pimms_file)
    if matches:
        first_entry = matches[0]
        print("SampleName:", first_entry[0])

        if isinstance(first_entry[1], pd.DataFrame):
            print("Columns in associated DataFrame:")
            print(", ".join(first_entry[1].columns))
        else:
            print("Second element is not a DataFrame. Type:", type(first_entry[1]))
    else:
        print("Matches list is empty.")


if __name__ == "__main__":
    main()
