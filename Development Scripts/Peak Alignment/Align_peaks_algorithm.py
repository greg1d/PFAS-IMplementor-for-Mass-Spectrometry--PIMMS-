import numpy as np
import pandas as pd
import plotly.graph_objects as go
import psutil
from scipy.sparse import lil_matrix
from scipy.spatial import distance
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors, sort_graph_by_row_values
from sklearn.preprocessing import MinMaxScaler


# Function to limit memory usage
def limit_memory_usage():
    """Calculates available memory to set a limit for processing."""
    mem = psutil.virtual_memory()
    available_memory = mem.available * 0.9  # Use 70% of available memory
    print(f"Available memory: {available_memory / (1024**2):.2f} MB")
    return available_memory


# Function to calculate m/z distance
def mz_distance(mz1, mz2, ppm_tolerance=1e-5):
    delta_mz = abs(mz2 - mz1)
    return delta_mz / (mz1 * ppm_tolerance)


# Function to calculate RT distance
def rt_distance(rt1, rt2, rt_tolerance=0.5):
    delta_rt = abs(rt2 - rt1)
    return delta_rt / rt_tolerance


# Function to calculate CCS distance
def ccs_distance(ccs1, ccs2, ccs_tolerance=0.02):
    delta_ccs = abs(ccs2 - ccs1)
    return delta_ccs / (ccs1 * ccs_tolerance)


# Create a sparse distance matrix
def create_distance_matrix_sparse(
    mz_values,
    rt_values,
    ccs_values,
    ppm_tolerance=1e-5,
    rt_tolerance=0.5,
    ccs_tolerance=0.02,
    eps_cutoff=None,  # Only store distances below this cutoff
):
    """
    Create a sparse distance matrix for large datasets.
    """
    mz_values = np.array(mz_values)
    rt_values = np.array(rt_values)
    ccs_values = np.array(ccs_values)

    n = len(mz_values)
    dist_matrix = lil_matrix((n, n), dtype=np.float32)  # Initialize sparse matrix

    for i in range(n):
        # Calculate distances for the current row
        mz_diff = np.abs(mz_values[i] - mz_values)
        rt_diff = np.abs(rt_values[i] - rt_values)
        ccs_diff = np.abs(ccs_values[i] - ccs_values)

        mz_dist = mz_diff / (mz_values[i] * ppm_tolerance)
        rt_dist = rt_diff / rt_tolerance
        ccs_dist = ccs_diff / (ccs_values[i] * ccs_tolerance)

        dist_row = np.sqrt(mz_dist**2 + rt_dist**2 + ccs_dist**2)

        # Store only distances below the cutoff in the sparse matrix
        if eps_cutoff is not None:
            below_cutoff = dist_row < eps_cutoff
            dist_matrix[i, below_cutoff] = dist_row[below_cutoff]
        else:
            dist_matrix[i, :] = dist_row

    return dist_matrix.tocsr()  # Convert to Compressed Sparse Row format


np.random.seed(42)
mz_clusters = []
rt_clusters = []
ccs_clusters = []
mz_center1, mz_center2 = 800.1, 801.3  # Close mz centers to create overlap
rt_center1, rt_center2 = 8.5, 8.5  # Close rt centers to create overlap
ccs_center1, ccs_center2 = 105, 105  # Close ccs centers to create overlap

# Define sizes for the clusters
cluster_size1 = np.random.randint(1000, 5000)
cluster_size2 = np.random.randint(4000, 5000)

# Generate the overlapping clusters
mz_clusters.append(np.random.normal(mz_center1, 0.01, cluster_size1))
rt_clusters.append(np.random.normal(rt_center1, 0.5, cluster_size1))
ccs_clusters.append(np.random.normal(ccs_center1, 2, cluster_size1))

mz_clusters.append(np.random.normal(mz_center2, 0.01, cluster_size2))
rt_clusters.append(np.random.normal(rt_center2, 0.5, cluster_size2))
ccs_clusters.append(np.random.normal(ccs_center2, 2, cluster_size2))

# Noise
mz_noise = np.random.uniform(0, 1600, 5)
rt_noise = np.random.uniform(0, 16, 5)
ccs_noise = np.random.uniform(0, 200, 5)

# Combine clusters and noise
mz_values = np.concatenate(mz_clusters + [mz_noise])
rt_values = np.concatenate(rt_clusters + [rt_noise])
ccs_values = np.concatenate(ccs_clusters + [ccs_noise])

# Print the total number of features
total_features = len(mz_values)
print(f"Total number of features: {total_features}")


# Combine clusters and noise
mz_values = np.concatenate(mz_clusters)
rt_values = np.concatenate(rt_clusters)
ccs_values = np.concatenate(ccs_clusters)

# Print the total number of features
total_features = len(mz_values)
print(f"Total number of features: {total_features}")

# Parameters
eps_cutoff = 1.732  # Adjusted EPS cutoff value for three dimensions
ppm_tolerance = 1e-5
rt_tolerance = 0.5
ccs_tolerance = 0.02

# Create distance matrix with memory limit
available_memory = limit_memory_usage()
memory_limit = available_memory * 0.9  # Use 10% of available memory

# Create sparse distance matrix
dist_matrix_sparse = create_distance_matrix_sparse(
    mz_values,
    rt_values,
    ccs_values,
    ppm_tolerance=ppm_tolerance,
    rt_tolerance=rt_tolerance,
    ccs_tolerance=ccs_tolerance,
    eps_cutoff=eps_cutoff,
)

# Sort the sparse matrix by row values
dist_matrix_sparse_sorted = sort_graph_by_row_values(
    dist_matrix_sparse, warn_when_not_sorted=False
)

# Perform DBSCAN clustering
dbscan = DBSCAN(eps=eps_cutoff, min_samples=2, metric="precomputed")
labels = dbscan.fit_predict(dist_matrix_sparse_sorted)

# Print the number of clusters
num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
print(f"Number of clusters: {num_clusters}")

# Parameters for drift tolerance
drift_mz_tolerance = 1.2 * ppm_tolerance
drift_rt_tolerance = 1.2 * rt_tolerance
drift_ccs_tolerance = 1.2 * ccs_tolerance

# Refine clusters using drift tolerance
for k in np.unique(labels):
    if k != -1:
        class_member_mask = labels == k
        cluster_mz = mz_values[class_member_mask]
        cluster_rt = rt_values[class_member_mask]
        cluster_ccs = ccs_values[class_member_mask]

        if len(cluster_mz) > 2 and len(cluster_rt) > 2 and len(cluster_ccs) > 2:
            # Calculate the core values of the cluster
            mz_core = np.percentile(cluster_mz, 50)
            rt_core = np.percentile(cluster_rt, 50)
            ccs_core = np.percentile(cluster_ccs, 50)
            print("mz core", mz_core, "rt core", rt_core, "CCS core", ccs_core)
            # Dynamic drift tolerances
            dynamic_mass_drift = drift_mz_tolerance * mz_core
            dynamic_ccs_drift = drift_ccs_tolerance * ccs_core

            # Exclude points exceeding the drift tolerance
            drift_mask = (
                (abs(cluster_mz - mz_core) <= dynamic_mass_drift)
                & (abs(cluster_rt - rt_core) <= drift_rt_tolerance)
                & (abs(cluster_ccs - ccs_core) <= dynamic_ccs_drift)
            )
            labels[class_member_mask] = np.where(drift_mask, k, -1)

# Combine data into a single array
points = np.vstack((mz_values, rt_values, ccs_values)).T

# Scale data using Min-Max Scaler
scaler = MinMaxScaler()
points_scaled = scaler.fit_transform(points)

# Calculate pairwise distances
pairwise_distances = distance.cdist(points_scaled, points_scaled, metric="euclidean")

# Adjust radius using a meaningful percentile
radius = np.percentile(pairwise_distances[pairwise_distances > 0], 1)  # 1st percentile

# Compute density using Nearest Neighbors
nbrs = NearestNeighbors(radius=radius).fit(points_scaled)

density = np.array(
    [len(nbrs.radius_neighbors([point])[0][0]) for point in points_scaled]
)

# Normalize density for coloring
density_min = density.min()
density_max = density.max()
if density_max != density_min:
    density_normalized = (density - density_min) / (density_max - density_min)
else:
    density_normalized = np.zeros_like(density)

df = pd.DataFrame(
    {
        "m/z": mz_values,
        "RT": rt_values,
        "CCS": ccs_values,
        "Cluster": labels,
        "Density": density_normalized,
    }
)

cluster_colors = [
    "red",
    "blue",
    "green",
    "purple",
    "orange",
    "cyan",
    "magenta",
    "yellow",
    "black",
    "pink",
]
df["Color"] = df["Cluster"].apply(
    lambda x: cluster_colors[x % len(cluster_colors)] if x != -1 else "grey"
)


# Option to color by density or cluster
color_by = "Cluster"  # Change to 'Cluster' to color by cluster

# Plot with Plotly
fig = go.Figure()
fig.add_trace(
    go.Scatter3d(
        x=df["m/z"],
        y=df["RT"],
        z=df["CCS"],
        mode="markers",
        marker=dict(
            size=2,
            color=df["Color"] if color_by == "Cluster" else df["Density"],
            colorscale="Viridis" if color_by == "Density" else None,
            colorbar=dict(title=color_by),
        ),
        text=df.apply(
            lambda row: f"m/z: {row['m/z']}, RT: {row['RT']}, CCS: {row['CCS']}, Cluster: {row['Cluster']}",
            axis=1,
        ),  # Hover text
        hoverinfo="text",
        name="Points",
    )
)

# Update layout
fig.update_layout(
    scene=dict(xaxis_title="m/z", yaxis_title="RT", zaxis_title="CCS"),
    title="3D Scatter Plot of scan",
)

fig.show()
