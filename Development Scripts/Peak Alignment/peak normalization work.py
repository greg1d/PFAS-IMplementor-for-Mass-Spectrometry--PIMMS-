import numpy as np
from sklearn.cluster import DBSCAN
import math
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import time


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
np.random.seed(42)  # For reproducibility

# Cluster 1
mz_cluster1 = np.random.normal(1020, 0.01, 500)
rt_cluster1 = np.random.normal(5, 0.5, 500)
ccs_cluster1 = np.random.normal(120, 2, 500)

# Cluster 2
mz_cluster2 = np.random.normal(1050, 0.01, 500)
rt_cluster2 = np.random.normal(10, 0.5, 500)
ccs_cluster2 = np.random.normal(150, 2, 500)

# Noise
mz_noise = np.random.uniform(1000, 1100, 200)
rt_noise = np.random.uniform(1, 16, 200)
ccs_noise = np.random.uniform(100, 200, 200)

# Combine clusters and noise
mz_values = np.concatenate([mz_cluster1, mz_cluster2, mz_noise])
rt_values = np.concatenate([rt_cluster1, rt_cluster2, rt_noise])
ccs_values = np.concatenate([ccs_cluster1, ccs_cluster2, ccs_noise])

eps_cutoff = 1.732  # Adjusted EPS cutoff value for three dimensions
ppm_tolerance = 1e-5
rt_tolerance = 0.5
ccs_tolerance = 0.02

# Calculate drift tolerances
drift_mz_tolerance = 1.5 * ppm_tolerance
drift_rt_tolerance = 1.5 * rt_tolerance
drift_ccs_tolerance = 1.5 * ccs_tolerance

# Measure time for creating distance matrix
start_time = time.time()
dist_matrix = create_distance_matrix(
    mz_values, rt_values, ccs_values, ppm_tolerance, rt_tolerance, ccs_tolerance
)
end_time = time.time()
print(f"Creating distance matrix took {end_time - start_time:.4f} seconds")

# Measure time for DBSCAN clustering
start_time = time.time()
dbscan = DBSCAN(eps=eps_cutoff, min_samples=1, metric="precomputed")
labels = dbscan.fit_predict(dist_matrix)
end_time = time.time()
print(f"DBSCAN clustering took {end_time - start_time:.4f} seconds")

# Adjust labels for clusters with fewer than 2 items
start_time = time.time()
unique_labels, counts = np.unique(labels, return_counts=True)
for label, count in zip(unique_labels, counts):
    if count < 2:
        labels[labels == label] = -1  # Mark as noise
end_time = time.time()
print(f"Adjusting labels took {end_time - start_time:.4f} seconds")

# Measure time for applying drift tolerance
start_time = time.time()
for k in unique_labels:
    if k != -1:
        class_member_mask = labels == k
        cluster_mz = mz_values[class_member_mask]
        cluster_rt = rt_values[class_member_mask]
        cluster_ccs = ccs_values[class_member_mask]

        if len(cluster_mz) > 2 and len(cluster_rt) > 2 and len(cluster_ccs) > 2:
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
end_time = time.time()
print(f"Applying drift tolerance took {end_time - start_time:.4f} seconds")

# Measure time for visualization
start_time = time.time()
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
end_time = time.time()
print(f"Visualization took {end_time - start_time:.4f} seconds")
