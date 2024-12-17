import pandas as pd
import matplotlib.pyplot as plt


def main():
    # Read the CSV file
    df = pd.read_csv("tests/Peak Alignment Testing Set.csv")

    # Separate m/z and CCS columns
    sample_mz_columns = df.columns[::2]  # Odd columns
    sample_ccs_columns = df.columns[1::2]  # Even columns

    # Print the extracted columns for verification
    print("Sample m/z columns:")
    print(sample_mz_columns)
    print("Sample CCS columns:")
    print(sample_ccs_columns)

    # Print the first few rows of the data
    print("First few rows of the data:")
    print(df.head())

    # Plot all the points in a scatter plot
    plt.figure(figsize=(10, 6))
    for mz_col, ccs_col in zip(sample_mz_columns, sample_ccs_columns):
        plt.scatter(df[mz_col], df[ccs_col], label=f"{mz_col} vs {ccs_col}")

    plt.xlabel("m/z")
    plt.ylabel("CCS")
    plt.title("Scatter Plot of m/z vs CCS")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
