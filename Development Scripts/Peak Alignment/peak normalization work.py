import numpy as np
from sklearn.cluster import DBSCAN
import math


# Function to calculate the m/z distance
def mz_distance(mz1, mz2, ppm_tolerance=1e-5):
    delta_mz = abs(mz2 - mz1)
    return delta_mz / (mz1 * ppm_tolerance)


# Function to calculate the RT distance
def rt_distance(rt1, rt2, rt_tolerance=0.5):
    delta_rt = abs(rt2 - rt1)
    return delta_rt / rt_tolerance


# Function to calculate the EPS distance
def calculate_eps(mz1, mz2, rt1, rt2, ppm_tolerance=1e-5, rt_tolerance=0.5):
    # Calculate individual distances
    mz_dist = mz_distance(mz1, mz2, ppm_tolerance)
    rt_dist = rt_distance(rt1, rt2, rt_tolerance)

    # Combine the distances using Euclidean distance
    eps = math.sqrt(mz_dist**2 + rt_dist**2)
    return eps


# Create a custom distance matrix for DBSCAN
def create_distance_matrix(mz_values, rt_values, ppm_tolerance=1e-5, rt_tolerance=0.5):
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
mz_values = [1000, 1000.02, 1001, 1000.01, 1001.01, 10000.1, 10000]  # m/z values
rt_values = [2, 2.5, 3, 2.2, 2.5, 2.5, 5]  # RT values
eps_cutoff = 1.414  # EPS cutoff value for DBSCAN

# Create distance matrix
dist_matrix = create_distance_matrix(mz_values, rt_values)

# Apply DBSCAN
dbscan = DBSCAN(eps=eps_cutoff, min_samples=1, metric="precomputed")
labels = dbscan.fit_predict(dist_matrix)

# Output the clustering results
print("Cluster labels:", labels)
