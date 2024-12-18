import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

# Example dataset
data = pd.DataFrame(
    {
        "x": [100, 101, 102, 200, 201, 204, 300, 303, 309, 312, 315, 318],
        "y": [50, 50.5, 51, 100, 101, 102, 200, 201, 202, 203, 204, 205],
    }
)

# Define scaling percentages
x_scale = 0.02  # 2% significance on x-axis
y_scale = 0.01  # 1% significance on y-axis

# 1. Transform the data using natural logarithm
data["x_log"] = np.log(data["x"])
data["y_log"] = np.log(data["y"])

# 2. Compute epsilon values in log-space
x_eps = np.log(1 + x_scale)  # Epsilon for x in log-space
y_eps = np.log(1 + y_scale)  # Epsilon for y in log-space

# Compute the combined epsilon using Euclidean distance
eps = np.sqrt(x_eps**2 + y_eps**2)

# 3. Feature matrix for clustering
X_log = data[["x_log", "y_log"]].values

# Apply DBSCAN with the computed epsilon
db = DBSCAN(eps=eps, min_samples=3).fit(X_log)

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
plt.title("DBSCAN Clustering Results")
plt.legend()
plt.grid(True)
plt.show()
