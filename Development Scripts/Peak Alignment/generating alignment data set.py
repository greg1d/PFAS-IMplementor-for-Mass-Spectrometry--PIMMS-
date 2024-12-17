import pandas as pd
import numpy as np
import os


def main():
    # Read the CSV file
    df = pd.read_csv(
        "Development Scripts\Peak Alignment\Peak Alignment Testing Set.csv"
    )

    # Extract the "RT", "CCS", and "m/z" columns
    rt_column = df["RT"]
    ccs_column = df["CCS"]
    mz_column = df["m/z"]

    # Repeat the process 20 times to create 20 sets of data points
    for i in range(1, 21):
        # Generate random values within the specified ranges
        rt_random = rt_column + np.random.uniform(-0.25, 0.25, size=len(rt_column))
        ccs_random = ccs_column * (
            1 + np.random.uniform(-0.02, 0.02, size=len(ccs_column))
        )
        mz_random = mz_column * (
            1 + np.random.uniform(-10e-6, 10e-6, size=len(mz_column))
        )

        # Add the generated values as new columns to the original DataFrame
        df[f"RT_{i}"] = rt_random
        df[f"CCS_{i}"] = ccs_random
        df[f"m/z_{i}"] = mz_random

    # Print the extracted columns for verification
    print("Original RT column:")
    print(rt_column.head())
    print("Original CCS column:")
    print(ccs_column.head())
    print("Original m/z column:")
    print(mz_column.head())

    # Print the generated values for verification
    print("Generated RT values (first set):")
    print(df["RT_1"].head())
    print("Generated CCS values (first set):")
    print(df["CCS_1"].head())
    print("Generated m/z values (first set):")
    print(df["m/z_1"].head())

    # Save the generated DataFrame to a CSV file in the same directory as the current script
    output_path = os.path.join(
        os.path.dirname(__file__), "generated_alignment_data_set.csv"
    )
    df.to_csv(output_path, index=False)
    print(f"Generated data saved to {output_path}")


if __name__ == "__main__":
    main()
