import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter
from matplotlib.font_manager import FontProperties
from scipy.spatial.distance import pdist, squareform


def normalize_data(df):
    # Separate m/z and CCS columns
    sample_mz_columns = df.columns[2::3]  # Every third column starting from 0
    sample_ccs_columns = df.columns[1::3]  # Every third column starting from 1

    # Combine the sample data for normalization
    combined_data = []
    for index, row in df.iterrows():
        mz_values = row[sample_mz_columns].dropna().values
        ccs_values = row[sample_ccs_columns].dropna().values
        if len(mz_values) == len(ccs_values):
            combined_data.append(np.vstack((mz_values, ccs_values)).T)
    if not combined_data:
        return None
    combined_data = np.vstack(combined_data)

    # Normalize the data
    normalized_data = np.copy(combined_data)
    normalized_data[:, 0] /= 10**-6
    # Normalize m/z by dividing by m/z * 10^-6
    normalized_data[:, 1] /= 0.02  # Normalize CCS by dividing by 0.02

    return normalized_data


def plot_normalized_data(normalized_data):
    # Debug: Print the normalized data coordinates to 10 decimal places
    print("Normalized Data Coordinates (first 5 points):")
    for point in normalized_data[:5]:
        print(f"x: {point[0]:.10f}, y: {point[1]:.10f}")

    # Plot the normalized data
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    # Load custom font
    font_path = "fonts/Montserrat-Regular.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    ax.scatter(
        normalized_data[:, 0],  # Normalized m/z on the x-axis
        normalized_data[:, 1],  # Normalized CCS on the y-axis
        color="b",
        edgecolor="k",
        label="Normalized Data",
    )

    ax.set_xlabel("Normalized m/z", labelpad=20, fontproperties=font_properties)
    ax.set_ylabel("Normalized CCS", fontproperties=font_properties)
    ax.set_title(
        "2D Scatter Plot of Normalized m/z and CCS", fontproperties=font_properties
    )

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    # Set tick labels font properties
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_properties)

    # Set x-axis limits to be ±10% of the max and min values in the x dimension
    x_min, x_max = np.min(normalized_data[:, 0]), np.max(normalized_data[:, 0])
    x_range = x_max - x_min
    ax.set_xlim(x_min - 0.1 * x_range, x_max + 0.1 * x_range)

    # Debug: Print the x-axis limits
    print("x_min:", x_min, "x_max:", x_max)
    print("x_range:", x_range)
    print("x-axis limits:", ax.get_xlim())

    plt.legend()
    plt.show()


def print_distances(normalized_data):
    # Calculate pairwise distances
    distances = pdist(normalized_data)
    distance_matrix = squareform(distances)

    # Print the distances
    print("Pairwise distances between points (first 5 points):")
    for i in range(min(5, len(distance_matrix))):
        for j in range(min(5, len(distance_matrix))):
            print(
                f"Distance between point {i} and point {j}: {distance_matrix[i, j]:.10f}"
            )


def main():
    # Read the CSV file
    df = pd.read_csv(
        r"Development Scripts\Peak Alignment\generated_alignment_data_set_short.csv"
    )

    # Normalize the data
    normalized_data = normalize_data(df)

    if normalized_data is not None:
        # Plot normalized data
        plot_normalized_data(normalized_data)

        print_distances(normalized_data)


if __name__ == "__main__":
    main()
