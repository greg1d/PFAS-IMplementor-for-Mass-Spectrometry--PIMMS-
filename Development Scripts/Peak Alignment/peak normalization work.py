import numpy as np
from scipy.sparse import lil_matrix
from sklearn.cluster import DBSCAN
from sklearn.neighbors import sort_graph_by_row_values
import plotly.graph_objects as go
import plotly.express as px
import psutil


# Function to limit memory usage
def limit_memory_usage():
    """Calculates available memory to set a limit for processing."""
    mem = psutil.virtual_memory()
    available_memory = mem.available * 0.7  # Use 80% of available memory
    print(f"Available memory: {available_memory / (1024 ** 2):.2f} MB")
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


# Generate synthetic data
np.random.seed(42)  # For reproducibility

# Generate 200 clusters
num_clusters = 20
mz_clusters = []
rt_clusters = []
ccs_clusters = []

for _ in range(num_clusters):
    mz_center = np.random.uniform(1500, 1550)
    rt_center = np.random.uniform(15, 16)
    ccs_center = np.random.uniform(195, 200)
    cluster_size = np.random.randint(30, 51)

    mz_clusters.append(np.random.normal(mz_center, 0.01, cluster_size))
    rt_clusters.append(np.random.normal(rt_center, 0.5, cluster_size))
    ccs_clusters.append(np.random.normal(ccs_center, 2, cluster_size))

# Noise
mz_noise = np.random.uniform(0, 1600, 5000)
rt_noise = np.random.uniform(0, 16, 5000)
ccs_noise = np.random.uniform(0, 200, 5000)

# Combine clusters and noise
mz_values = np.concatenate(mz_clusters + [mz_noise])
rt_values = np.concatenate(rt_clusters + [rt_noise])
ccs_values = np.concatenate(ccs_clusters + [ccs_noise])

total_features = len(mz_values)
print(f"Total number of features: {total_features}")

# Parameters
eps_cutoff = 1.732  # Adjusted EPS cutoff value for three dimensions
ppm_tolerance = 1e-5
rt_tolerance = 0.5
ccs_tolerance = 0.02

# Create distance matrix with memory limit
available_memory = limit_memory_usage()
memory_limit = available_memory * 0.1  # Use 10% of available memory

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
unique_labels = np.unique(labels)
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
