import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter
from matplotlib.font_manager import FontProperties


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

    # Load custom font
    font_path = "fonts/Montserrat-Bold.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    ax.set_xlabel(
        "m/z", labelpad=20, fontproperties=font_properties
    )  # Increase labelpad for spacing
    ax.set_ylabel("CCS", fontproperties=font_properties)
    ax.set_zlabel("RT", fontproperties=font_properties)
    ax.set_title("3D Scatter Plot of m/z, CCS, and RT", fontproperties=font_properties)

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    # Set tick labels font properties
    for label in ax.get_xticklabels() + ax.get_yticklabels() + ax.get_zticklabels():
        label.set_fontproperties(font_properties)

    # Rotate the graph
    ax.view_init(elev=20, azim=20)  # Set the elevation and azimuthal angles

    plt.show()


if __name__ == "__main__":
    main()
