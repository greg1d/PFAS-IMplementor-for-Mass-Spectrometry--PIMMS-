import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

# Example dataset
data = pd.DataFrame(
    {
        "x": [100, 101, 102, 200, 201, 204, 300, 300, 307],
        "y": [50, 50.5, 51, 100, 101, 102, 200, 201, 202],
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
db = DBSCAN(eps=eps, min_samples=2).fit(X_log)

# Assign cluster labels
data["cluster"] = db.labels_

print(data[["x", "y", "cluster"]])
