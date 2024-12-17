import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import hdbscan
from matplotlib.ticker import FormatStrFormatter
from matplotlib.font_manager import FontProperties


def align_peaks_algorithm(df):
    # Separate m/z, CCS, and RT columns
    sample_mz_columns = df.columns[::3]  # Every third column starting from 0
    sample_ccs_columns = df.columns[1::3]  # Every third column starting from 1
    sample_rt_columns = df.columns[2::3]  # Every third column starting from 2

    # Combine the sample data for clustering
    combined_data = []
    row_indices = []
    for index, row in df.iterrows():
        mz_values = row[sample_mz_columns].dropna().values
        ccs_values = row[sample_ccs_columns].dropna().values
        rt_values = row[sample_rt_columns].dropna().values
        if len(mz_values) == len(ccs_values) == len(rt_values):
            combined_data.append(np.vstack((mz_values, ccs_values, rt_values)).T)
            row_indices.extend([index] * len(mz_values))
        else:
            print(
                f"Row {index} has mismatched lengths: m/z={len(mz_values)}, CCS={len(ccs_values)}, RT={len(rt_values)}"
            )
    if not combined_data:
        print("No valid data to cluster.")
        return
    combined_data = np.vstack(combined_data)
    row_indices = np.array(row_indices)

    # Scale the data according to the specified distances
    combined_data[:, 0] /= 1e-5  # Scale m/z axis by 1e-5
    combined_data[:, 1] /= 0.02  # Scale CCS axis by 2%
    combined_data[:, 2] /= 0.5  # Scale RT axis by 0.5 minutes

    # Perform HDBSCAN clustering with explicit range parameters
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=5)
    cluster_labels = clusterer.fit_predict(combined_data)

    # Collect outliers data
    outliers = []

    for cluster in set(cluster_labels):
        if cluster == -1:
            continue  # Skip noise points
        cluster_data = combined_data[cluster_labels == cluster]
        cluster_rows = row_indices[cluster_labels == cluster]
        unique_rows, counts = np.unique(cluster_rows, return_counts=True)
        majority_row = unique_rows[np.argmax(counts)]
        outlier_indices = cluster_rows != majority_row

        # Print row distribution for debugging
        print(f"Cluster {cluster} row distribution:")
        for row, count in zip(unique_rows, counts):
            print(f"Row {row}: {count} entries")

        # Collect outliers data
        outlier_data = cluster_data[outlier_indices]
        outlier_rows = cluster_rows[outlier_indices]
        for data, row in zip(outlier_data, outlier_rows):
            outliers.append([row, data[0] * 1e-5, data[1] * 0.02, data[2] * 0.5])

    # Export outliers to CSV
    outliers_df = pd.DataFrame(outliers, columns=["Row", "m/z", "CCS", "RT"])
    outliers_df.to_csv("outliers.csv", index=False)
    print("Outliers exported to 'outliers.csv'")

    return combined_data, cluster_labels, row_indices


def plot_clusters(combined_data, cluster_labels):
    # Plot the clustering result
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")

    # Load custom font
    font_path = "fonts/Montserrat-Regular.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    for cluster in set(cluster_labels):
        if cluster == -1:
            continue  # Skip noise points
        cluster_data = combined_data[cluster_labels == cluster]

        # Plot cluster points
        ax.scatter(
            cluster_data[:, 0] * 1e-5,  # Scale back m/z axis
            cluster_data[:, 1] * 0.02,  # Scale back CCS axis
            cluster_data[:, 2] * 0.5,  # Scale back RT axis
            label=f"Cluster {cluster}",
        )

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
    ax.view_init(elev=20, azim=40)  # Set the elevation and azimuthal angles

    plt.show()


def plot_outliers():
    # Read the outliers CSV file
    outliers_df = pd.read_csv("outliers.csv")

    # Load custom font
    font_path = "fonts/Montserrat-Regular.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    # Plot the outliers
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(
        outliers_df["m/z"],  # m/z on the x-axis
        outliers_df["CCS"],  # CCS on the y-axis
        outliers_df["RT"],  # RT on the z-axis
        color="r",
        edgecolor="k",
        label="Outliers",
    )

    ax.set_xlabel(
        "m/z", labelpad=20, fontproperties=font_properties
    )  # Increase labelpad for spacing
    ax.set_ylabel("CCS", fontproperties=font_properties)
    ax.set_zlabel("RT", fontproperties=font_properties)
    ax.set_title(
        "3D Scatter Plot of Outliers (m/z, CCS, RT)", fontproperties=font_properties
    )

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    # Set tick labels font properties
    for label in ax.get_xticklabels() + ax.get_yticklabels() + ax.get_zticklabels():
        label.set_fontproperties(font_properties)

    # Rotate the graph
    ax.view_init(elev=20, azim=40)  # Set the elevation and azimuthal angles

    plt.legend()
    plt.show()


def main():
    # Read the CSV file
    df = pd.read_csv("tests/Peak Alignment Testing Set.csv")

    # Print the first few rows of the data
    print("First few rows of the data:")
    print(df.head())

    # Call the align_peaks_algorithm function
    combined_data, cluster_labels, row_indices = align_peaks_algorithm(df)

    # Plot clusters
    plot_clusters(combined_data, cluster_labels)

    # Plot outliers
    plot_outliers()


if __name__ == "__main__":
    main()
