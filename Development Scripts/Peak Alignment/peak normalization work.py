import numpy as np
from sklearn.cluster import DBSCAN
import math
import time
import plotly.graph_objects as go
import plotly.express as px
import psutil


def limit_memory_usage():
    mem = psutil.virtual_memory()
    available_memory = mem.available * 0.8
    print("Available memory:", available_memory)
    return available_memory


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
    mz_values = np.array(mz_values)
    rt_values = np.array(rt_values)
    ccs_values = np.array(ccs_values)

    # Calculate pairwise differences
    mz_diff = np.abs(mz_values[:, np.newaxis] - mz_values)
    rt_diff = np.abs(rt_values[:, np.newaxis] - rt_values)
    ccs_diff = np.abs(ccs_values[:, np.newaxis] - ccs_values)

    # Calculate distances
    mz_dist = mz_diff / (mz_values[:, np.newaxis] * ppm_tolerance)
    rt_dist = rt_diff / rt_tolerance
    ccs_dist = ccs_diff / (ccs_values[:, np.newaxis] * ccs_tolerance)

    # Combine distances using Euclidean distance
    dist_matrix = np.sqrt(mz_dist**2 + rt_dist**2 + ccs_dist**2)

    return dist_matrix


np.random.seed(42)  # For reproducibility

# Cluster 1
mz_cluster1 = np.random.normal(1020, 0.01, 500)
rt_cluster1 = np.random.normal(5, 0.5, 500)
ccs_cluster1 = np.random.normal(120, 2, 500)

# Cluster 2
mz_cluster2 = np.random.normal(1050, 0.01, 5000)
rt_cluster2 = np.random.normal(10, 0.5, 5000)
ccs_cluster2 = np.random.normal(150, 2, 5000)

# Noise
mz_noise = np.random.uniform(1000, 1100, 5000)
rt_noise = np.random.uniform(1, 16, 5000)
ccs_noise = np.random.uniform(100, 200, 5000)

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

# Visualization of the clusters in 3D using Plotly
fig = go.Figure()

# Generate a colormap for clusters
colors = px.colors.qualitative.Plotly

# Plot noise points first
noise_mask = labels == -1
xyz_noise = np.array([mz_values, rt_values, ccs_values]).T[noise_mask]
fig.add_trace(
    go.Scatter3d(
        x=xyz_noise[:, 0],
        y=xyz_noise[:, 1],
        z=xyz_noise[:, 2],
        mode="markers",
        marker=dict(size=5, color="grey"),
        name="Noise",
    )
)

# Plot clusters
for k in unique_labels:
    if k != -1:
        class_member_mask = labels == k
        xyz = np.array([mz_values, rt_values, ccs_values]).T[class_member_mask]

        # Assign a unique color to each cluster
        color = colors[k % len(colors)]
        name = f"Cluster {k}"

        fig.add_trace(
            go.Scatter3d(
                x=xyz[:, 0],
                y=xyz[:, 1],
                z=xyz[:, 2],
                mode="markers",
                marker=dict(size=5, color=color),
                name=name,
            )
        )

fig.update_layout(
    scene=dict(xaxis_title="m/z", yaxis_title="RT", zaxis_title="CCS"),
    title="DBSCAN Clustering of m/z, RT, and CCS Values",
)

fig.show()

end_time = time.time()
print(f"Visualization took {end_time - start_time:.4f} seconds")
