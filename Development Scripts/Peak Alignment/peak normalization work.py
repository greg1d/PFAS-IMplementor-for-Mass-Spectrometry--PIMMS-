import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

# Example dataset
data = pd.DataFrame(
    {
        "x": [300, 300, 300, 300, 300],
        "y": [1000, 1000.1, 1000, 1000, 1000],
    }
)

# Define tolerances
x_tolerance = 0.02 * 300  # 2% of x values
y_tolerance = 10 / 1e6 * 1000  # 10 ppm of y values

# Scale the data
data["x_scaled"] = data["x"] / x_tolerance  # Normalize x by its tolerance
data["y_scaled"] = data["y"] / y_tolerance  # Normalize y by its tolerance

# Combine scaled data for DBSCAN
X_scaled = data[["x_scaled", "y_scaled"]].values

# Compute epsilon in the scaled space
eps = np.sqrt(2)  # Adjust as needed for clustering sensitivity

# Apply DBSCAN in scaled space
db = DBSCAN(eps=eps, min_samples=2).fit(X_scaled)

# Assign cluster labels
data["cluster"] = db.labels_

# Plot the results
plt.figure(figsize=(8, 6))

# Scatter plot of the data points colored by their cluster labels
for cluster_label in data["cluster"].unique():
    cluster_data = data[data["cluster"] == cluster_label]
    plt.scatter(
        cluster_data["x"],
        cluster_data["y"],
        label=f"Cluster {cluster_label}" if cluster_label != -1 else "Noise",
        s=100,
        alpha=0.7,
        edgecolors="k",
    )

# Add axis labels and legend
plt.xlabel("X")
plt.ylabel("Y")
plt.title("DBSCAN Clustering Results with Proper Scaling")
plt.legend()
plt.grid(True)
plt.show()
