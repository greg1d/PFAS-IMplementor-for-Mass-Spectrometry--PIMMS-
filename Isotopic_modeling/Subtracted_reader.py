import time

import pandas as pd
from Modules.binary_logic_puller import (
    analyze_peaks,  # Assuming the functions are in binary_logic_puller.py
)


def main():
    start_time = time.time()  # Start the timer

    file_path = "data\Edited full blank subtracted data set.csv"  # Update this path to your local CSV file
    z_range = range(1, 20)  # This will check for z = 1 to 5
    mass_error_ppm = 10
    rt_tolerance = 0.2
    ccs_tolerance = 0.02

    # Load the data to get RT, CCS, and ID values
    data_df = pd.read_csv(file_path)
    rt_ccs_mapping = data_df.set_index("ID").to_dict("index")

    # Find the column that contains ".d.DeMP"
    demp_column = [col for col in data_df.columns if ".d.DeMP" in col][0]

    # Run the operation
    groups, unrelated_features, total_calculations = analyze_peaks(
        file_path, z_range, mass_error_ppm, rt_tolerance, ccs_tolerance
    )

    results = []
    for idx, group in enumerate(groups):
        for peak, peak_id, peak_demp in group:
            # Extract RT, CCS, ID, and .d.DeMP values from the mapping using the ID
            rt_value = rt_ccs_mapping.get(peak_id, {}).get("RT", "N/A")
            ccs_value = rt_ccs_mapping.get(peak_id, {}).get("CCS", "N/A")
            id_value = rt_ccs_mapping.get(peak_id, {}).get("ID", "N/A")
            demp_value = rt_ccs_mapping.get(peak_id, {}).get(demp_column, "N/A")
            results.append(
                {
                    "Group": idx + 1,
                    "Peak": peak,
                    "ID": peak_id,
                    "RT": rt_value,
                    "CCS": ccs_value,
                    "Peak Intensity": demp_value,
                }
            )

    # Print the results
    print(f"Total groups identified: {len(groups)}")
    print(f"Total unrelated features: {unrelated_features}")
    print(f"Total calculations performed: {total_calculations}")

    end_time = time.time()  # End the timer

    results_df = pd.DataFrame(results)
    results_df.to_csv("analyzed_peaks_results.csv", index=False)
    print("Results saved to analyzed_peaks_results.csv")
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Time taken to run the script: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()
