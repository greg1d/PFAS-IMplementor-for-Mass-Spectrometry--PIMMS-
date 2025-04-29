import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load and clean
file_path = r"presentations\smearing_raw_data.csv"
df = pd.read_csv(file_path)
df = df[["Mass", "Drift", "Abundance"]].dropna()

# Pivot into grid (this only works if grid is regular)
pivot = df.pivot_table(index="Drift", columns="Mass", values="Abundance")

X = pivot.columns.values
Y = pivot.index.values
X, Y = np.meshgrid(X, Y)
Z = pivot.values

# Plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, Z, cmap="Greys", edgecolor="k", linewidth=0.2)

ax.set_xlabel("Mass (m/z)")
ax.set_ylabel("Drift Time (ms)")
ax.set_zlabel("Abundance")
ax.set_title("3D Surface: Mass vs Drift vs Abundance")

plt.tight_layout()
plt.show()
