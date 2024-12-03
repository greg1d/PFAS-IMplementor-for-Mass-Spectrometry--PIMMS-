import time

import pandas as pd
from Modules.binary_logic_puller import analyze_peaks
from tqdm import tqdm


def main():
    file_path = "data/Edited full blank subtracted data set.csv"  # Update this path to your local CSV file
    z_range = range(1, 5)  # This will check for z = 1 to 5
    mass_error_ppm = 10  # Define the mass error in ppm

    # Load the data to get RT, CCS, and ID values
    data_df = pd.read_csv(file_path)
    rt_ccs_mapping = (
        data_df.groupby("m/z")[["RT", "CCS", "ID"]]
        .agg(lambda x: x.iloc[0])
        .to_dict("index")
    )

    # Start the progress bar
    with tqdm(total=100, desc="Processing peaks") as pbar:
        start_time = time.time()

        groups, unrelated_features, total_calculations = analyze_peaks(
            file_path, z_range, mass_error_ppm
        )

        # Simulate progress update
        pbar.update(100)

        end_time = time.time()
        elapsed_time = end_time - start_time

    # Print the number of groups identified
    print(f"Number of groups identified: {len(groups)}")

    # Print the groups of related peaks
    print("Groups of related peaks:")
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}: {sorted(group)}")

    # Print the number of unrelated features
    print(f"Number of unrelated features: {unrelated_features}")

    # Print the number of calculations performed
    print(f"Number of calculations performed: {total_calculations}")

    print(f"Script completed in {elapsed_time:.2f} seconds")

    # Export the results to a CSV file
    results = []
    for idx, group in enumerate(groups):
        for peak in group:
            # Extract RT, CCS, and ID values from the mapping
            rt_value = rt_ccs_mapping.get(peak, {}).get("RT", "N/A")
            ccs_value = rt_ccs_mapping.get(peak, {}).get("CCS", "N/A")
            id_value = rt_ccs_mapping.get(peak, {}).get("ID", "N/A")
            results.append(
                {
                    "Group": idx + 1,
                    "Peak": peak,
                    "RT": rt_value,
                    "CCS": ccs_value,
                    "ID": id_value,
                }
            )

    results_df = pd.DataFrame(results)
    results_df.to_csv("analyzed_peaks_results.csv", index=False)
    print("Results saved to analyzed_peaks_results.csv")


if __name__ == "__main__":
    main()
