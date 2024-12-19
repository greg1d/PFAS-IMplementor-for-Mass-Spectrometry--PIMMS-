import numpy as np
from sklearn.cluster import DBSCAN
import math
import matplotlib.pyplot as plt


# Function to calculate the m/z distance
def mz_distance(mz1, mz2, ppm_tolerance=1e-4):
    delta_mz = abs(mz2 - mz1)
    return delta_mz / (mz1 * ppm_tolerance)


# Function to calculate the RT distance
def rt_distance(rt1, rt2, rt_tolerance=0.5):
    delta_rt = abs(rt2 - rt1)
    return delta_rt / rt_tolerance


# Function to calculate the EPS distance
def calculate_eps(mz1, mz2, rt1, rt2, ppm_tolerance=1e-4, rt_tolerance=0.5):
    # Calculate individual distances
    mz_dist = mz_distance(mz1, mz2, ppm_tolerance)
    rt_dist = rt_distance(rt1, rt2, rt_tolerance)

    # Combine the distances using Euclidean distance
    eps = math.sqrt(mz_dist**2 + rt_dist**2)
    return eps


# Create a custom distance matrix for DBSCAN
def create_distance_matrix(mz_values, rt_values, ppm_tolerance=1e-4, rt_tolerance=0.5):
    n = len(mz_values)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            eps = calculate_eps(
                mz_values[i],
                mz_values[j],
                rt_values[i],
                rt_values[j],
                ppm_tolerance,
                rt_tolerance,
            )
            dist_matrix[i, j] = eps
            dist_matrix[j, i] = eps  # Distance matrix is symmetric

    return dist_matrix


# Example usage
mz_values = [1000, 1000.2, 1001, 1000.1, 1001.01, 1002.1]  # m/z values
rt_values = [2, 2.5, 3, 2.2, 2.5, 2.5]  # RT values
eps_cutoff = 1.414  # EPS cutoff value for DBSCAN

# Create distance matrix
dist_matrix = create_distance_matrix(mz_values, rt_values)

# Apply DBSCAN
dbscan = DBSCAN(eps=eps_cutoff, min_samples=1, metric="precomputed")
labels = dbscan.fit_predict(dist_matrix)
print("Cluster labels:", labels)

# Adjust labels for clusters with fewer than 2 items
unique_labels, counts = np.unique(labels, return_counts=True)
for label, count in zip(unique_labels, counts):
    if count < 2:
        labels[labels == label] = -1  # Mark as noise

# Visualization of the clusters
plt.figure(figsize=(10, 6))
unique_labels = set(labels)
colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

for k, col in zip(unique_labels, colors):
    if k == -1:
        # Black used for noise.
        col = [0, 0, 0, 1]

    class_member_mask = labels == k

    xy = np.array([mz_values, rt_values]).T[class_member_mask]
    plt.scatter(
        xy[:, 0],
        xy[:, 1],
        c=[col],
        edgecolor="k",
        label=f"Cluster {k}" if k != -1 else "Noise",
    )

plt.xlabel("m/z")
plt.ylabel("RT")
plt.title("DBSCAN Clustering of m/z and RT Values")
plt.legend()
plt.show()
