import hdbscan
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist, squareform


def align_peaks_algorithm(df, mz_scale_factor=1e-5, ccs_scale_factor=0.02):
    # Separate m/z and CCS columns
    sample_mz_columns = df.columns[2::3]  # Every third column starting from 0
    sample_ccs_columns = df.columns[1::3]  # Every third column starting from 1

    # Combine the sample data for clustering
    combined_data = []
    row_indices = []
    for index, row in df.iterrows():
        mz_values = row[sample_mz_columns].dropna().values
        ccs_values = row[sample_ccs_columns].dropna().values
        print(
            f"Row {index} - m/z values: {mz_values}, CCS values: {ccs_values}"
        )  # Debugging
        if len(mz_values) == len(ccs_values):
            combined_data.append(np.vstack((mz_values, ccs_values)).T)
            row_indices.extend([index] * len(mz_values))
        else:
            print(
                f"Row {index} has mismatched lengths: m/z={len(mz_values)}, CCS={len(ccs_values)}"
            )
    if not combined_data:
        print("No valid data to cluster.")
        return None, None, None
    combined_data = np.vstack(combined_data)
    row_indices = np.array(row_indices)

    # Print the data before scaling
    print("Data before scaling:")
    print(combined_data[:5])  # Print first 5 rows for brevity

    # Dynamic scaling for m/z and CCS
    combined_data[:, 0] /= mz_scale_factor  # Scale m/z axis
    combined_data[:, 1] /= ccs_scale_factor  # Scale CCS axis

    # Print the data after scaling
    print("Data after scaling:")
    print(combined_data[:5])  # Print first 5 rows for brevity

    # Perform HDBSCAN clustering with explicit range parameters
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5)  # Smaller clusters
    cluster_labels = clusterer.fit_predict(combined_data)

    # Collect outliers data
    outliers = []
    distances_data = []

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
            outliers.append(
                [row, data[0] * mz_scale_factor, data[1] * ccs_scale_factor]
            )

        # Calculate and print maximum distances in each dimension
        max_mz_dist = np.max(cluster_data[:, 0]) - np.min(cluster_data[:, 0])
        max_ccs_dist = np.max(cluster_data[:, 1]) - np.min(cluster_data[:, 1])
        print(
            f"Cluster {cluster} max distances - m/z: {max_mz_dist * mz_scale_factor}, CCS: {max_ccs_dist * ccs_scale_factor}"
        )

        # Filter out points that do not meet the criteria
        for point in cluster_data:
            if (
                np.max(np.abs(cluster_data[:, 0] - point[0])) * mz_scale_factor > 1e-5
                or np.max(np.abs(cluster_data[:, 1] - point[1])) * ccs_scale_factor > 8
            ):
                outliers.append(
                    [
                        row_indices[cluster_labels == cluster][0],
                        point[0] * mz_scale_factor,
                        point[1] * ccs_scale_factor,
                    ]
                )
                print(f"Outlier point: {point}")

        # Calculate pairwise distances within the cluster
        pairwise_distances = squareform(pdist(cluster_data))
        for i in range(len(cluster_data)):
            for j in range(i + 1, len(cluster_data)):
                distances_data.append([cluster, i, j, pairwise_distances[i, j]])

    # Export outliers to CSV
    outliers_df = pd.DataFrame(outliers, columns=["Row", "m/z", "CCS"])
    outliers_df.to_csv("outliers.csv", index=False)
    print("Outliers exported to 'outliers.csv'")

    # Export distances to CSV
    distances_df = pd.DataFrame(
        distances_data, columns=["Cluster", "Point1", "Point2", "Distance"]
    )
    distances_df.to_csv("distances.csv", index=False)
    print("Distances exported to 'distances.csv'")

    return combined_data, cluster_labels, row_indices, mz_scale_factor, ccs_scale_factor


def plot_clusters(combined_data, cluster_labels, mz_scale_factor, ccs_scale_factor):
    # Plot the clustering result
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    # Load custom font
    font_path = "fonts/Montserrat-Regular.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    unique_labels = set(cluster_labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = [0, 0, 0, 1]

        class_member_mask = cluster_labels == k

        xy = combined_data[class_member_mask]
        ax.scatter(
            xy[:, 0] * mz_scale_factor,  # Scale back m/z axis
            xy[:, 1] * ccs_scale_factor,  # Scale back CCS axis
            color=tuple(col),
            edgecolor="k",
            label=f"Cluster {k}" if k != -1 else "Noise",
        )

        # Draw convex hull around the cluster if there are enough unique points
        if (
            len(np.unique(xy, axis=0)) >= 3
        ):  # Convex hull requires at least 3 unique points
            hull = ConvexHull(xy)
            for simplex in hull.simplices:
                ax.plot(
                    xy[simplex, 0] * mz_scale_factor,
                    xy[simplex, 1] * ccs_scale_factor,
                    "k-",
                )

    ax.set_xlabel(
        "m/z", labelpad=20, fontproperties=font_properties
    )  # Increase labelpad for spacing
    ax.set_ylabel("CCS", fontproperties=font_properties)
    ax.set_title("2D Scatter Plot of m/z and CCS", fontproperties=font_properties)

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    # Set tick labels font properties
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_properties)

    plt.legend()
    plt.show()


def plot_outliers(mz_scale_factor, ccs_scale_factor):
    # Read the outliers CSV file
    outliers_df = pd.read_csv("outliers.csv")

    # Load custom font
    font_path = "fonts/Montserrat-Regular.ttf"
    font_properties = FontProperties(fname=font_path, size=10)

    # Plot the outliers
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    ax.scatter(
        outliers_df["m/z"],  # m/z on the x-axis
        outliers_df["CCS"],  # CCS on the y-axis
        color="r",
        edgecolor="k",
        label="Outliers",
    )

    ax.set_xlabel(
        "m/z", labelpad=20, fontproperties=font_properties
    )  # Increase labelpad for spacing
    ax.set_ylabel("CCS", fontproperties=font_properties)
    ax.set_title(
        "2D Scatter Plot of Outliers (m/z, CCS)", fontproperties=font_properties
    )

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    # Set tick labels font properties
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_properties)

    plt.legend()
    plt.show()


def plot_raw_data(df):
    # Extract the "m/z" and "CCS" columns
    sample_mz_columns = df.columns[2::3]  # Every third column starting from 0
    sample_ccs_columns = df.columns[1::3]  # Every third column starting from 1

    # Combine the sample data for plotting
    combined_data = []
    for index, row in df.iterrows():
        mz_values = row[sample_mz_columns].dropna().values
        ccs_values = row[sample_ccs_columns].dropna().values
        if len(mz_values) == len(ccs_values):
            combined_data.append(np.vstack((mz_values, ccs_values)).T)
    if not combined_data:
        print("No valid data to plot.")
        return
    combined_data = np.vstack(combined_data)

    # Plot the raw data
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    ax.scatter(
        combined_data[:, 0],  # m/z on the x-axis
        combined_data[:, 1],  # CCS on the y-axis
        color="b",
        edgecolor="k",
        label="Raw Data",
    )

    ax.set_xlabel("m/z", labelpad=20)
    ax.set_ylabel("CCS")
    ax.set_title("2D Scatter Plot of Raw Data (m/z, CCS)")

    # Format the m/z axis to use general format numbers reported to 2 decimal places
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    plt.legend()
    plt.show()


def main():
    # Read the CSV file
    df = pd.read_csv(
        r"Development Scripts\Peak Alignment\generated_alignment_data_set_short.csv"
    )

    # Print the first few rows of the data
    print("First few rows of the data:")
    print(df.head())

    # Plot raw data
    plot_raw_data(df)

    # Call the align_peaks_algorithm function
    combined_data, cluster_labels, row_indices, mz_scale, ccs_scale = (
        align_peaks_algorithm(df, mz_scale_factor=1e-5, ccs_scale_factor=0.02)
    )

    if combined_data is not None:
        # Plot clusters
        plot_clusters(combined_data, cluster_labels, mz_scale, ccs_scale)


if __name__ == "__main__":
    main()
