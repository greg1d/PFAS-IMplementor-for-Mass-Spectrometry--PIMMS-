import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    # Read the CSV file
    df = pd.read_csv("tests/Peak Alignment Testing Set.csv")

    # Separate m/z, CCS, and RT columns
    sample_mz_columns = df.columns[::3]  # Every third column starting from 0
    sample_ccs_columns = df.columns[1::3]  # Every third column starting from 1
    sample_rt_columns = df.columns[2::3]  # Every third column starting from 2

    # Print the extracted columns for verification
    print("Sample m/z columns:")
    print(sample_mz_columns)
    print("Sample CCS columns:")
    print(sample_ccs_columns)
    print("Sample RT columns:")
    print(sample_rt_columns)

    # Print the first few rows of the data
    print("First few rows of the data:")
    print(df.head())

    # Plot all the points in a 3D scatter plot, color-coordinated by row
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    cmap = plt.get_cmap("viridis")
    num_rows = len(df)
    colors = cmap(np.linspace(0, 1, num_rows))

    for index, (row, color) in enumerate(zip(df.iterrows(), colors)):
        mz_values = row[1][sample_mz_columns].dropna()
        ccs_values = row[1][sample_ccs_columns].dropna()
        rt_values = row[1][sample_rt_columns].dropna()
        if len(mz_values) == len(ccs_values) == len(rt_values):
            ax.scatter(
                mz_values, ccs_values, rt_values, label=f"Row {index + 1}", color=color
            )

    ax.set_xlabel("m/z")
    ax.set_ylabel("CCS")
    ax.set_zlabel("RT")
    ax.set_title("3D Scatter Plot of m/z, CCS, and RT")
    ax.legend()
    plt.show()


if __name__ == "__main__":
    main()
