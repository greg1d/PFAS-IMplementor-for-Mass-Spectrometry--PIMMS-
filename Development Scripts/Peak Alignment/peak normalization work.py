import numpy as np
from sklearn.cluster import DBSCAN
import math
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm


# Function to calculate the m/z distance
def mz_distance(mz1, mz2, ppm_tolerance=1e-5):
    delta_mz = abs(mz2 - mz1)
    return delta_mz / (mz1 * ppm_tolerance)


# Function to calculate the RT distance
def rt_distance(rt1, rt2, rt_tolerance=0.5):
    delta_rt = abs(rt2 - rt1)
    return delta_rt / rt_tolerance


# Function to calculate the CCS distance
def ccs_distance(ccs1, ccs2, ccs_tolerance=0.02):
    delta_ccs = abs(ccs2 - ccs1)
    return delta_ccs / (ccs1 * ccs_tolerance)


# Function to calculate the EPS distance
def calculate_eps(
    mz1,
    mz2,
    rt1,
    rt2,
    ccs1,
    ccs2,
    ppm_tolerance=1e-5,
    rt_tolerance=0.5,
    ccs_tolerance=0.02,
):
    # Calculate individual distances
    mz_dist = mz_distance(mz1, mz2, ppm_tolerance)
    rt_dist = rt_distance(rt1, rt2, rt_tolerance)
    ccs_dist = ccs_distance(ccs1, ccs2, ccs_tolerance)

    # Combine the distances using Euclidean distance
    eps = math.sqrt(mz_dist**2 + rt_dist**2 + ccs_dist**2)
    return eps


# Create a custom distance matrix for DBSCAN
def create_distance_matrix(
    mz_values,
    rt_values,
    ccs_values,
    ppm_tolerance=1e-5,
    rt_tolerance=0.5,
    ccs_tolerance=0.02,
):
    n = len(mz_values)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            eps = calculate_eps(
                mz_values[i],
                mz_values[j],
                rt_values[i],
                rt_values[j],
                ccs_values[i],
                ccs_values[j],
                ppm_tolerance,
                rt_tolerance,
                ccs_tolerance,
            )
            dist_matrix[i, j] = eps
            dist_matrix[j, i] = eps  # Distance matrix is symmetric

    return dist_matrix


# Example usage
mz_values = np.array(
    [1000, 1000, 1000, 1000.01, 1000.02, 1000.03, 1000.04, 1000.05, 1000.06]
)  # m/z values
rt_values = np.array([2, 2, 2, 2.5, 2.5, 2.2, 2.5, 2.5, 2.5])  # RT values
ccs_values = np.array([100, 101, 102, 100, 101, 102, 100, 102, 100])  # CCS values
eps_cutoff = 1.732  # Adjusted EPS cutoff value for three dimensions
ppm_tolerance = 1e-5
rt_tolerance = 0.5
ccs_tolerance = 0.02

# Calculate drift tolerances
drift_mz_tolerance = 1.5 * ppm_tolerance
drift_rt_tolerance = 1.5 * rt_tolerance
drift_ccs_tolerance = 1.5 * ccs_tolerance

# Create distance matrix
dist_matrix = create_distance_matrix(
    mz_values, rt_values, ccs_values, ppm_tolerance, rt_tolerance, ccs_tolerance
)

# Apply DBSCAN
dbscan = DBSCAN(eps=eps_cutoff, min_samples=1, metric="precomputed")
labels = dbscan.fit_predict(dist_matrix)
print("Cluster labels:", labels)

# Adjust labels for clusters with fewer than 2 items
unique_labels, counts = np.unique(labels, return_counts=True)
for label, count in zip(unique_labels, counts):
    if count < 2:
        labels[labels == label] = -1  # Mark as noise

# Apply drift tolerance
for k in unique_labels:
    if k != -1:
        class_member_mask = labels == k
        cluster_mz = mz_values[class_member_mask]
        cluster_rt = rt_values[class_member_mask]
        cluster_ccs = ccs_values[class_member_mask]

        # Calculate the mean of the cluster
        mz_core = np.percentile(cluster_mz, 25)
        ccs_core = np.percentile(cluster_ccs, 25)
        rt_core = np.percentile(cluster_rt, 25)
        dynamic_mass_drift = drift_mz_tolerance * mz_core
        dynamic_css_drift = drift_ccs_tolerance * ccs_core

        # Exclude points that exceed the drift tolerance
        drift_mask = (
            (abs(cluster_mz - mz_core) <= dynamic_mass_drift)
            & (abs(cluster_rt - rt_core) <= drift_rt_tolerance)
            & (abs(cluster_ccs - ccs_core) <= dynamic_css_drift)
        )
        labels[class_member_mask] = np.where(drift_mask, k, -1)
        print(dynamic_mass_drift)
        print("cluster mean mass", mz_core)
        print(abs(cluster_mz - mz_core))
# Visualization of the clusters in 3D
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection="3d")
unique_labels = set(labels)

# Normalize distances for colormap
norm = Normalize(vmin=0, vmax=eps_cutoff)
cmap = cm.get_cmap("coolwarm_r")  # Use the reversed coolwarm colormap

for k in unique_labels:
    if k == -1:
        # Grey used for noise.
        col = [0.5, 0.5, 0.5, 1]
    else:
        # Black used for clusters.
        col = [0, 0, 0, 1]

    class_member_mask = labels == k

    xyz = np.array([mz_values, rt_values, ccs_values]).T[class_member_mask]
    scatter = ax.scatter(
        xyz[:, 0],
        xyz[:, 1],
        xyz[:, 2],
        c=[col],
        edgecolor="k",
        label=f"Cluster {k}" if k != -1 else "Noise",
    )

    # Draw edges between points in the same cluster
    if k != -1:  # Skip noise points
        for i in range(len(xyz)):
            for j in range(i + 1, len(xyz)):
                distance = np.linalg.norm(xyz[i] - xyz[j])
                line_color = cmap(norm(distance))
                ax.plot(
                    [xyz[i, 0], xyz[j, 0]],
                    [xyz[i, 1], xyz[j, 1]],
                    [xyz[i, 2], xyz[j, 2]],
                    color=line_color,
                    linewidth=1,
                )


ax.set_xlabel("m/z")
ax.set_ylabel("RT")
ax.set_zlabel("CCS")
ax.set_title("DBSCAN Clustering of m/z, RT, and CCS Values")
plt.show()
