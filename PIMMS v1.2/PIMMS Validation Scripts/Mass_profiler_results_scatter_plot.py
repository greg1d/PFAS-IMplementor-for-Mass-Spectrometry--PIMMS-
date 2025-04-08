import pandas as pd
import matplotlib.pyplot as plt

# File path
file_path = r"PIMMS Validation work\Comparison test output\Bar chart data.csv"

# Read CSV
df = pd.read_csv(file_path, header=None)

# Extract data
accuracy_values = df.iloc[1, 1:].astype(float).tolist()
feature_counts = df.iloc[2, 1:].astype(int).tolist()
colors = ["#3E4A89", "#E41A1C", "#4DAF4A", "#FF7F00"]

# Labels
x_labels = ["1", "2", "3", "4"]

# Create figure and axes with transparent background
fig, ax1 = plt.subplots(figsize=(2.7, 4), facecolor="none")

# Bar plot (Accuracy)
bars = ax1.bar(
    x_labels,
    accuracy_values,
    color=colors,
    edgecolor="black",
    linewidth=1.2,
    width=0.6,
)

# Format primary y-axis (Accuracy)
ax1.set_ylabel("Accuracy (%)", weight="bold", fontsize=10)
ax1.tick_params(axis="both", width=2, labelsize=8)
ax1.set_ylim(0, 100)

# Set font weight for tick labels
for label in ax1.get_xticklabels() + ax1.get_yticklabels():
    label.set_fontweight("bold")
    label.set_fontsize(8)

# Style spines
for side in ["left", "bottom", "right"]:
    ax1.spines[side].set_linewidth(2)
ax1.spines["top"].set_visible(False)

# Secondary y-axis for feature counts
ax2 = ax1.twinx()
ax2.plot(
    x_labels,
    feature_counts,
    marker="o",
    linestyle="--",
    color="black",
    linewidth=2,
    label="Feature Count",
)
ax2.set_ylabel("Number of Features", weight="bold", fontsize=10)
ax2.tick_params(axis="y", width=2, labelsize=8)

# Set font weight for secondary axis tick labels
for label in ax2.get_yticklabels():
    label.set_fontweight("bold")
    label.set_fontsize(8)

ax2.spines["top"].set_visible(False)
ax2.set_ylim(0, 12000)
plt.savefig(
    "PIMMS v1.2\PIMMS Validation Scripts\Mass_profiler_results_scatter_plot.png",
    dpi=300,
    transparent=True,
    bbox_inches="tight",
)

plt.tight_layout()
plt.show()
