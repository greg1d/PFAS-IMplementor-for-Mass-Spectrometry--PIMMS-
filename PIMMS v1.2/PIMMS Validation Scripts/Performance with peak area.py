import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# === Load CSV ===
file_path = r"PIMMS Validation work\Comparison test output\Summary of models.csv"
df = pd.read_csv(file_path)

# === X and Y data ===
x = df["Skyline Average Intensity"]
y_columns = [
    "Common Organic Molecules - no intensity cutoff - 9077 features",
]
colors = ["#3E4A89"]  # Line color

# === Plot ===
fig, ax = plt.subplots(figsize=(3.5, 4))
for col, color in zip(y_columns, colors):
    y = df[col]
    valid = x > 0
    x_valid = x[valid]
    y_valid = y[valid]

    # Sort by x for proper line plotting
    sorted_indices = np.argsort(x_valid)
    x_sorted = np.array(x_valid)[sorted_indices]
    y_sorted = np.array(y_valid)[sorted_indices]

    # Scatter points with higher z-order (above axis)
    ax.scatter(x_sorted, y_sorted, color=color, alpha=1, edgecolor="none", zorder=3)

    # Line connecting points
    ax.plot(x_sorted, y_sorted, color=color, linewidth=2, label=col, zorder=2)

# Spine styling
for side in ["left", "bottom"]:
    ax.spines[side].set_linewidth(2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Tick styling
ax.tick_params(axis="both", width=2)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontweight("bold")
    label.set_fontsize(8)

# === Format axes ===
ax.set_xscale("log")
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.set_xlabel("Feature Peak Area", fontsize=10, weight="bold")
ax.set_ylabel("Accuracy (%)", fontsize=10, weight="bold")
ax.set_ylim(-2, 105)
plt.tight_layout()
plt.savefig(
    "PIMMS v1.2\PIMMS Validation Scripts\Performance with peak area.png",
    transparent=True,
)
plt.show()
